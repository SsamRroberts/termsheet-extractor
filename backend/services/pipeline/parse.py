"""PDF extraction service using pymupdf4llm.

Converts termsheet PDFs to structured markdown text ready for LLM consumption.
"""

import logging
import tempfile
from pathlib import Path

import pymupdf4llm

logger = logging.getLogger(__name__)


def extract_markdown(pdf_bytes: bytes, filename: str = "document.pdf") -> str:
    """Extract structured markdown from a PDF.

    Writes bytes to a temp file (pymupdf4llm requires a file path),
    then extracts markdown with tables, headers, and formatting preserved.

    Args:
        pdf_bytes: Raw PDF file content.
        filename: Original filename for logging.

    Returns:
        Markdown string of the full document.

    Raises:
        ValueError: If the PDF is empty or cannot be parsed.
    """
    if not pdf_bytes:
        raise ValueError("PDF content is empty")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()

        logger.info(f"Extracting markdown from '{filename}' ({len(pdf_bytes)} bytes)")
        md_text = pymupdf4llm.to_markdown(tmp.name)

    if not md_text or not md_text.strip():
        raise ValueError(f"No text extracted from '{filename}' — the PDF may be image-only or corrupted")

    logger.info(f"Extracted {len(md_text)} chars from '{filename}'")
    return md_text


def extract_markdown_from_path(pdf_path: str | Path) -> str:
    """Extract structured markdown from a PDF file on disk.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Markdown string of the full document.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the PDF cannot be parsed.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(f"Extracting markdown from '{pdf_path.name}'")
    md_text = pymupdf4llm.to_markdown(str(pdf_path))

    if not md_text or not md_text.strip():
        raise ValueError(f"No text extracted from '{pdf_path.name}'")

    logger.info(f"Extracted {len(md_text)} chars from '{pdf_path.name}'")
    return md_text
