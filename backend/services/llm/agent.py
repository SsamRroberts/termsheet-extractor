"""LLM agent orchestration for termsheet extraction."""

import logging
import time

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from core.config import settings
from services.llm.prompts import SYSTEM_PROMPT
from schemas.termsheet import TermsheetData
from services.llm.tools import make_tools

logger = logging.getLogger(__name__)


def _error_handler(e: Exception) -> str:
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

    tools = make_tools(markdown_text)

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
            handle_errors=_error_handler,
            tool_message_content="Termsheet data received and validated",
        ),
    )

    logger.info("Invoking LLM agent...")
    t0 = time.monotonic()
    result = agent.invoke({"messages": messages}, config={"recursion_limit": 300})
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
