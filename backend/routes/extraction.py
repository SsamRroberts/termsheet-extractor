"""Termsheet upload and extraction endpoints."""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db.db import get_db
from schemas.product import ExtractionResponse, JobCreatedResponse
from services.pipeline import run_sync, stream
from utils.job_store import create_job, pop_job

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload-termsheet", response_model=ExtractionResponse)
async def upload_termsheet(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a termsheet PDF — extract, validate, and persist."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    filename = file.filename or "termsheet.pdf"
    logger.info(f"Received termsheet: {filename} ({len(contents)} bytes)")

    return run_sync(contents, filename, db)


@router.post("/upload-termsheet-async", response_model=JobCreatedResponse)
async def upload_termsheet_async(
    file: UploadFile = File(...),
):
    """Accept a PDF, store it in memory, and return a job_id immediately."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    filename = file.filename or "termsheet.pdf"
    job_id = create_job(filename, contents)
    logger.info(f"Created async job {job_id} for {filename} ({len(contents)} bytes)")

    return JobCreatedResponse(job_id=job_id, filename=filename, size_bytes=len(contents))


@router.get("/extraction-stream/{job_id}")
def extraction_stream(job_id: str, db: Session = Depends(get_db)):
    """SSE endpoint that runs the extraction pipeline and streams progress."""
    job = pop_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or already consumed")

    filename, contents = job
    return StreamingResponse(
        stream(contents, filename, db),
        media_type="text/event-stream",
    )
