"""LLM-based structured data extraction from termsheet markdown.

Takes the markdown output of pdf_extractor (pymupdf4llm) and uses a LangChain
agent to extract structured product, event, and underlying data matching
the database schema.
"""

import logging
import time
from datetime import date

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, ValidationError

from core.config import settings

logger = logging.getLogger(__name__)

# ── Structured output models (mirror DB schema) ─────────────────────────────


class Underlying(BaseModel):
    bbg_code: str = Field(description="Bloomberg ticker code, e.g. 'SX5E INDEX'")
    weight: float | None = Field(None, description="Portfolio weight as a decimal (e.g. 0.5 for 50%)")
    initial_price: float = Field(description="RI Initial Value / starting price for the underlying")


class Event(BaseModel):
    event_type: str = Field(
        description=(
            "One of: 'coupon', 'auto_early_redemption', 'knock_in', 'final_redemption'"
        )
    )
    event_level_pct: float | None = Field(
        None,
        description="Barrier or trigger level as a percentage (e.g. 75.0 for 75%)",
    )
    event_strike_pct: float | None = Field(
        None,
        description="Strike percentage if applicable (e.g. 100.0 for 100%)",
    )
    event_date: date = Field(description="Valuation date for this event (YYYY-MM-DD)")
    event_amount: float | None = Field(
        None,
        description="Payment amount or rate as a percentage (e.g. 2.0375 for 2.0375%)",
    )
    event_payment_date: date | None = Field(
        None,
        description="Payment/settlement date if different from event_date (YYYY-MM-DD)",
    )


class Product(BaseModel):
    product_isin: str = Field(description="12-character ISIN code, e.g. 'XS3184638594'")
    sedol: str | None = Field(None, description="7-character SEDOL code")
    short_description: str | None = Field(None, description="Short product name/title")
    issuer: str | None = Field(None, description="Issuer legal entity name")
    issue_date: date = Field(description="Issue date (YYYY-MM-DD)")
    currency: str = Field(description="3-letter ISO currency code, e.g. 'GBP'")
    maturity: date = Field(description="Maturity date (YYYY-MM-DD)")
    product_type: str | None = Field(None, description="Product type, e.g. 'Structured Notes'")
    word_description: str | None = Field(
        None,
        description="Full text description of the product from the termsheet header",
    )


class TermsheetData(BaseModel):
    """Complete structured extraction from a termsheet PDF."""

    product: Product
    underlyings: list[Underlying]
    events: list[Event]


# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a financial data extraction specialist. You will receive the full \
markdown text of a structured product termsheet. Extract ALL relevant data \
into the structured format requested.

## Extraction rules

### Product
- Extract the ISIN code (12 characters starting with two letters).
- Extract the SEDOL code if present (7 characters).
- The issuer is the legal entity issuing the notes (not the guarantor or dealer).
- Currency is the 3-letter Specified Notes Currency.
- Issue Date and Maturity Date are explicitly labelled.
- short_description: use the product title/heading (e.g. "Phoenix on Index Basket due 2032").
- word_description: the opening paragraph describing what the notes are.
- product_type: the Instrument type (e.g. "Structured Notes").

### Underlyings
- Extract every underlying reference item from the basket table.
- bbg_code: the Bloomberg code exactly as shown (e.g. "SX5E INDEX").
- initial_price: the RI Initial Value.
- weight: only if explicitly stated; otherwise null.

### Events
Extract every scheduled event. Use these event_type values:

1. **"coupon"** — each row in the Coupon Valuation / Interest Payment Dates table.
   - event_date = Coupon Valuation Date
   - event_payment_date = Interest Payment Date
   - event_amount = the conditional coupon rate (e.g. 2.0375)
   - event_level_pct = Coupon Barrier percentage (e.g. 75.0)

2. **"auto_early_redemption"** — each row in the Automatic Early Redemption table.
   - event_date = Automatic Early Redemption Valuation Date
   - event_payment_date = Automatic Early Redemption Date
   - event_level_pct = Automatic Early Redemption Trigger percentage (e.g. 100.0)
   - event_amount = AER Percentage (e.g. 100.0)

3. **"knock_in"** — the knock-in barrier event at maturity.
   - event_date = Redemption Valuation Date
   - event_level_pct = Knock-in level percentage (e.g. 65.0)

4. **"final_redemption"** — the final maturity redemption.
   - event_date = Redemption Valuation Date / Maturity Date
   - event_strike_pct = Put Strike Percentage if applicable

Be precise with dates (YYYY-MM-DD format). Extract every row — do not \
summarise or skip rows from tables.\
"""


# ── Error handler ───────────────────────────────────────────────────────────


def termsheet_error_handler(e: Exception) -> str:
    """Custom error handler for termsheet extraction validation."""
    if isinstance(e, ValidationError):
        error_details = "\n".join(
            f"{field['loc'][0]}: {field['msg']}"
            for field in e.errors()
        )
        logger.warning("Validation failed (%d errors), asking LLM to retry: %s", len(e.errors()), error_details)
        return f"""Invalid termsheet data format:
{error_details}

Please ensure your extraction has:
- product: with valid ISIN, dates, currency, etc.
- underlyings: list of underlyings with bbg_code and initial_price
- events: list of events with valid event_type, dates, and levels"""
    logger.error("Unexpected error during extraction: %s", e)
    return f"Error: {str(e)}"


# ── Extraction function ─────────────────────────────────────────────────────


def extract_termsheet_data(markdown_text: str) -> TermsheetData:
    """Extract structured termsheet data from markdown using an LLM agent.

    Args:
        markdown_text: Markdown output from pdf_extractor / pymupdf4llm.

    Returns:
        TermsheetData with product, underlyings, and events.

    Raises:
        ValueError: If the LLM fails to return valid structured data.
    """
    logger.info("Starting LLM extraction (%d chars of markdown)", len(markdown_text))

    system_prompt = f"""{SYSTEM_PROMPT}

IMPORTANT: You must call the TermsheetData tool exactly ONCE with your final answer.
Do not call TermsheetData multiple times.
Do not call any other tools after making your extraction."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=markdown_text),
    ]

    logger.info("Initialising model: %s via %s", settings.LLM_MODEL, settings.LLM_API_URL)
    model = init_chat_model(
        model=settings.LLM_MODEL,
        model_provider="openai",
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_URL,
    )

    agent = create_agent(
        model,
        tools=[],
        response_format=ToolStrategy(
            TermsheetData,
            handle_errors=termsheet_error_handler,
            tool_message_content="Termsheet data received and validated",
        ),
    )

    logger.info("Invoking LLM agent...")
    t0 = time.monotonic()
    result = agent.invoke({"messages": messages})
    elapsed = time.monotonic() - t0
    logger.info("LLM agent returned in %.1fs", elapsed)

    structured = result["structured_response"]
    logger.info(
        "Extraction complete: product=%s, %d underlyings, %d events",
        structured.product.product_isin,
        len(structured.underlyings),
        len(structured.events),
    )

    return structured
