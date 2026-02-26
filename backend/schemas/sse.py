"""Typed SSE event models mirroring the frontend SseEvent union."""

import json
from typing import Any, Literal

from pydantic import BaseModel


class SseProgressEvent(BaseModel):
    stage: str
    progress: int


class SseCompleteEvent(BaseModel):
    stage: Literal["complete"] = "complete"
    progress: Literal[100] = 100
    data: dict[str, Any]


class SseValidationFailedEvent(BaseModel):
    stage: Literal["validation_failed"] = "validation_failed"
    progress: Literal[100] = 100
    data: dict[str, Any]


class SseErrorEvent(BaseModel):
    stage: Literal["error"] = "error"
    message: str


def sse_event(model: BaseModel) -> str:
    """Serialise a Pydantic model instance to SSE ``data:`` format."""
    return f"data: {json.dumps(model.model_dump(mode='json'))}\n\n"
