"""Multi-step termsheet ingest pipeline (PDF → markdown → LLM → validate → persist)."""

import logging
from typing import Generator

from fastapi import HTTPException
from sqlalchemy.orm import Session

from schemas.product import (
    ExtractionResponse,
    ValidationIssueOut,
    ValidationResultOut,
)
from schemas.sse import (
    SseCompleteEvent,
    SseErrorEvent,
    SseProgressEvent,
    SseValidationFailedEvent,
    sse_event,
)
from utils.markdown_store import save_markdown
from services.llm import extract_termsheet_data
from services.pipeline.parse import extract_markdown
from services.pipeline.persist import persist_extraction
from services.pipeline.validate import validate_termsheet

logger = logging.getLogger(__name__)


def run_sync(
    contents: bytes, filename: str, db: Session
) -> ExtractionResponse:
    """Run the full 7-step extraction pipeline synchronously."""

    # 1. PDF → markdown
    try:
        markdown_text = extract_markdown(contents, filename=filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # 2. Save markdown blob under "pending" before LLM call
    save_markdown("pending", filename, markdown_text)

    # 3. LLM extraction
    try:
        termsheet_data = extract_termsheet_data(markdown_text)
    except Exception as exc:
        logger.error(f"LLM extraction failed: {exc}")
        raise HTTPException(status_code=422, detail=f"LLM extraction failed: {exc}")

    # 4. Re-save under correct ISIN
    blob_path = save_markdown(termsheet_data.product.product_isin, filename, markdown_text)

    # 5. Validate
    validation = validate_termsheet(termsheet_data, db)

    # 6. If validation errors → return 422 with data + validation (no DB write)
    if not validation.is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "filename": filename,
                "size_bytes": len(contents),
                "status": "validation_failed",
                "product_isin": termsheet_data.product.product_isin,
                "approved": False,
                "data": termsheet_data.model_dump(mode="json"),
                "validation": validation.to_dict(),
            },
        )

    # 7. Persist with approved=False
    persist_extraction(termsheet_data, filename, blob_path, "success", db)

    return ExtractionResponse(
        filename=filename,
        size_bytes=len(contents),
        status="extracted",
        product_isin=termsheet_data.product.product_isin,
        approved=False,
        data=termsheet_data.model_dump(mode="json"),
        validation=ValidationResultOut(
            is_valid=validation.is_valid,
            issues=[
                ValidationIssueOut(
                    field=i.field, rule=i.rule, message=i.message, severity=i.severity,
                )
                for i in validation.issues
            ],
        ),
    )


def stream(
    contents: bytes, filename: str, db: Session
) -> Generator[str, None, None]:
    """SSE generator that runs the extraction pipeline and yields progress events."""
    try:
        # 1. PDF → markdown
        yield sse_event(SseProgressEvent(stage="extracting_pdf", progress=15))
        try:
            markdown_text = extract_markdown(contents, filename=filename)
        except ValueError as exc:
            yield sse_event(SseErrorEvent(message=f"PDF extraction failed: {exc}"))
            return

        # 2. Save markdown blob under "pending"
        yield sse_event(SseProgressEvent(stage="saving_blob", progress=30))
        save_markdown("pending", filename, markdown_text)

        # 3. LLM extraction (the slow step)
        yield sse_event(SseProgressEvent(stage="llm_extraction", progress=50))
        try:
            termsheet_data = extract_termsheet_data(markdown_text)
        except Exception as exc:
            logger.error(f"LLM extraction failed: {exc}")
            yield sse_event(SseErrorEvent(message=f"LLM extraction failed: {exc}"))
            return

        # 4. Re-save under correct ISIN
        blob_path = save_markdown(termsheet_data.product.product_isin, filename, markdown_text)

        # 5. Validate
        yield sse_event(SseProgressEvent(stage="validation", progress=80))
        validation = validate_termsheet(termsheet_data, db)

        if not validation.is_valid:
            yield sse_event(SseValidationFailedEvent(
                data={
                    "filename": filename,
                    "size_bytes": len(contents),
                    "status": "validation_failed",
                    "product_isin": termsheet_data.product.product_isin,
                    "approved": False,
                    "data": termsheet_data.model_dump(mode="json"),
                    "validation": validation.to_dict(),
                },
            ))
            return

        # 6. Persist
        yield sse_event(SseProgressEvent(stage="persisting", progress=90))
        persist_extraction(termsheet_data, filename, blob_path, "success", db)

        yield sse_event(SseCompleteEvent(
            data={
                "filename": filename,
                "size_bytes": len(contents),
                "status": "extracted",
                "product_isin": termsheet_data.product.product_isin,
                "approved": False,
                "data": termsheet_data.model_dump(mode="json"),
                "validation": validation.to_dict(),
            },
        ))
    except Exception as exc:
        logger.exception(f"Unexpected error in extraction stream: {exc}")
        yield sse_event(SseErrorEvent(message=str(exc)))
