"""LLM-based structured data extraction from termsheet markdown.

Takes the markdown output of pdf_extractor (pymupdf4llm) and uses a LangChain
agent to extract structured product, event, and underlying data matching
the database schema.
"""

import logging
import re
import time
from datetime import date

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
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
            "One of: 'strike', 'coupon', 'auto_early_redemption', 'knock_in'"
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
    short_description: str | None = Field(None, description="Product title from the document heading")
    issuer: str | None = Field(None, description="Short issuer name, e.g. 'BBVA' not the full legal entity")
    issue_date: date = Field(description="Issue date (YYYY-MM-DD)")
    currency: str = Field(description="3-letter ISO currency code, e.g. 'GBP'")
    maturity: date = Field(description="Maturity date (YYYY-MM-DD)")
    product_type: str | None = Field(None, description="Product category, e.g. 'Phoenix Autocall', 'Reverse Convertible'")
    word_description: str | None = Field(
        None,
        description="Full text description of the product from the termsheet header",
    )


class TermsheetData(BaseModel):
    """Complete structured extraction from a termsheet PDF."""

    product: Product
    underlyings: list[Underlying]
    events: list[Event]


# ── Document search tools ────────────────────────────────────────────────────


def _make_tools(markdown: str):
    """Create document search tools that close over the markdown text."""

    lines = markdown.splitlines()

    @tool
    def search_termsheet(query: str) -> str:
        """Search the termsheet for lines matching a keyword query.
        Returns matching lines with ±5 lines of context.
        Use this to find specific values like ISIN, dates, percentages, or any field."""
        query_lower = query.lower()
        matches = [i for i, line in enumerate(lines) if query_lower in line.lower()]

        if not matches:
            return f"No matches found for '{query}'."

        # Cap at 10 matches
        matches = matches[:10]

        results = []
        for match_idx in matches:
            start = max(0, match_idx - 5)
            end = min(len(lines), match_idx + 6)
            chunk = "\n".join(
                f"{'>>>' if j == match_idx else '   '} {lines[j]}"
                for j in range(start, end)
            )
            results.append(chunk)

        return f"Found {len(matches)} match(es) for '{query}':\n\n" + "\n---\n".join(results)

    @tool
    def read_section(heading: str) -> str:
        """Read a specific section of the termsheet by its heading.
        Uses fuzzy matching — you don't need the exact heading text.
        Returns everything from the heading to the next same-level heading."""
        heading_lower = heading.lower()

        # Find all markdown headings and their line numbers
        section_starts = []
        for i, line in enumerate(lines):
            if re.match(r"^#{1,3}\s", line):
                section_starts.append(i)

        # Find the best matching heading
        best_idx = None
        best_score = 0
        for start in section_starts:
            line_lower = lines[start].lower()
            terms = heading_lower.split()
            matched_terms = sum(1 for t in terms if t in line_lower)
            score = matched_terms / len(terms) if terms else 0
            if score > best_score:
                best_score = score
                best_idx = start

        if best_idx is None or best_score == 0:
            return f"No section matching '{heading}' found. Use list_sections() to see available headings."

        # Find the end of this section (next same-level or higher heading)
        heading_level = len(re.match(r"^(#+)", lines[best_idx]).group(1))
        end_idx = len(lines)
        for start in section_starts:
            if start > best_idx:
                other_level = len(re.match(r"^(#+)", lines[start]).group(1))
                if other_level <= heading_level:
                    end_idx = start
                    break

        section_text = "\n".join(lines[best_idx:end_idx])
        return f"Section '{lines[best_idx].strip()}':\n\n{section_text}"

    @tool
    def list_sections() -> str:
        """List all section headings in the termsheet.
        Use this first to understand the document structure before searching."""
        headings = []
        for i, line in enumerate(lines):
            if re.match(r"^#{1,3}\s", line):
                headings.append(f"  Line {i}: {line.strip()}")

        if not headings:
            return "No markdown headings found in this document."

        return "Document sections:\n" + "\n".join(headings)

    @tool
    def read_lines(start: int, end: int) -> str:
        """Read a range of lines from the termsheet (1-indexed, inclusive).
        Use after search_termsheet to read broader context around a match.
        For example, if a search hit is at line 135, call read_lines(120, 160)
        to see the full surrounding prose and tables."""
        start_idx = max(0, start - 1)  # convert to 0-indexed
        end_idx = min(len(lines), end)
        if start_idx >= end_idx:
            return "Invalid range. Start must be less than end."
        selected = lines[start_idx:end_idx]
        numbered = [f"{i + start_idx + 1:4d} | {line}" for i, line in enumerate(selected)]
        return "\n".join(numbered)

    return [search_termsheet, read_section, list_sections, read_lines]


# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a financial data extraction specialist. You have access to search \
tools that let you query a structured product termsheet. Your job is to \
extract ALL relevant data into the TermsheetData format.

Work through the following phases using your tools:

## Phase 1: Explore
Call list_sections() to understand the document structure.

## Phase 2: Product details
Search for each product field:
- search for "ISIN" to find the ISIN code (12 characters starting with two letters)
- search for "SEDOL" to find the SEDOL code (7 characters)
- The issuer is the entity after "Issuer" — use the SHORT name (e.g. "BBVA"), \
not the full legal entity
- search for "Currency" to find the 3-letter currency code
- search for "Issue Date" and "Maturity Date" for dates
- short_description: use the product title/heading from the top of the document \
(e.g. "6Y FTSE / Eurostoxx Phoenix 8.15% Note")
- product_type: classify the product (e.g. "Phoenix Autocall" for a Phoenix \
with autocall features)
- word_description: the opening paragraph describing what the notes are

## Phase 3: Underlyings
Search for the underlying/basket table. For each underlying:
- bbg_code: Bloomberg code as shown, e.g. "SX5E Index" or "UKX Index". \
Format as "[CODE] Index" — remove square brackets if present
- initial_price: the RI Initial Value
- weight: only if explicitly stated; otherwise null

## Phase 4: Events

### Phase 4a — Collect ALL barrier & trigger percentages FIRST
Before extracting any event rows, search for and record each of these values. \
They are usually in PROSE text, NOT inside date tables. Use read_lines() to \
widen context around search hits if needed.

1. **Put Strike percentage**: search for "Put Strike Percentage" in the \
underlyings table. Typically 100%.
2. **Coupon barrier**: search for "Coupon Barrier" or "Barrier Condition". \
The percentage is in the prose ABOVE the coupon dates table (e.g. "greater \
than or equal to 75%").
3. **Autocall trigger**: search for "Automatic Early Redemption Trigger". \
Look in the AER table column header or the prose. Record the percentage for \
each row (often the same for all rows, e.g. 100%).
4. **Knock-in barrier**: search for "Knock-in" or "Knock-in Event". The \
percentage is in a prose sentence (e.g. "less than 65.00%").
5. **Coupon amount**: search for the coupon rate near "Rate of Interest" \
(e.g. 2.0375%).

You MUST have concrete values for all five before proceeding. If a search \
returns no result, try read_lines() around the Interest or Redemption sections.

### Phase 4b — Strike event
Search for "Strike Date". Create ONE event:
- event_type = "strike"
- event_date = the Strike Date (may reference another date like Trade Date)
- event_level_pct = the Put Strike percentage from 4a (typically 100.0)
- event_strike_pct = the Put Strike percentage from 4a (typically 100.0)

### Phase 4c — Coupon events
Read the Interest section and extract EVERY row from the Coupon Valuation / \
Interest Payment Dates table. Apply the barrier and amount from Phase 4a to \
EVERY coupon row:
- event_type = "coupon"
- event_date = Coupon Valuation Date
- event_payment_date = Interest Payment Date
- event_amount = the coupon rate from 4a (e.g. 2.0375)
- event_level_pct = the Coupon Barrier from 4a (e.g. 75.0)

ALSO: the final coupon coincides with the Redemption Valuation Date — it is \
NOT in the coupon table. Search for "Redemption Valuation Date" to find this \
date and add it as an additional coupon event. Its payment date is the \
Maturity Date.

### Phase 4d — Autocall events
Extract EVERY row from the Automatic Early Redemption table:
- event_type = "auto_early_redemption"
- event_date = Automatic Early Redemption Valuation Date
- event_payment_date = Automatic Early Redemption Date
- event_level_pct = the AER Trigger percentage from 4a (per row if it varies)
- event_amount = AER Percentage from the table

### Phase 4e — Knock-in event
Create ONE event:
- event_type = "knock_in"
- event_date = Redemption Valuation Date
- event_payment_date = Maturity Date
- event_level_pct = the Knock-in barrier from 4a (e.g. 65.0)

### Phase 4f — Verify before submitting
Check your extracted events against this checklist:
- [ ] Strike event has BOTH event_level_pct AND event_strike_pct populated
- [ ] EVERY coupon event has event_level_pct populated (the barrier)
- [ ] EVERY autocall event has event_level_pct populated (the trigger)
- [ ] Knock-in event has event_level_pct populated (the barrier)
- [ ] No event has event_level_pct = null unless it genuinely has no barrier
If any are missing, go back and search again before submitting.

## Phase 5: Submit
Once you have gathered ALL data and passed the Phase 4f checklist, call \
TermsheetData with the complete extraction.

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

    tools = _make_tools(markdown_text)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            "Extract all structured product data from this termsheet. "
            "Use your search tools to find each required field. "
            "Work through all 5 phases before submitting."
        )),
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
        tools=tools,
        response_format=ToolStrategy(
            TermsheetData,
            handle_errors=termsheet_error_handler,
            tool_message_content="Termsheet data received and validated",
        ),
    )

    logger.info("Invoking LLM agent...")
    t0 = time.monotonic()
    result = agent.invoke({"messages": messages}, config={"recursion_limit": 30})
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
