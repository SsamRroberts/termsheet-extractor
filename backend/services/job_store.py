"""In-memory job store for async upload → SSE extraction flow."""

from __future__ import annotations

import uuid
from threading import Lock

_lock = Lock()
_jobs: dict[str, tuple[str, bytes]] = {}


def create_job(filename: str, pdf_bytes: bytes) -> str:
    """Store a PDF and return a unique job ID."""
    job_id = uuid.uuid4().hex
    with _lock:
        _jobs[job_id] = (filename, pdf_bytes)
    return job_id


def pop_job(job_id: str) -> tuple[str, bytes] | None:
    """Remove and return the job data, or None if not found."""
    with _lock:
        return _jobs.pop(job_id, None)
