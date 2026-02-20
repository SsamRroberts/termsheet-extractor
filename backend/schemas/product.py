"""Pydantic response schemas for product endpoints."""

from datetime import date
from typing import Any

from pydantic import BaseModel


class UnderlyingOut(BaseModel):
    bbg_code: str
    weight: float | None = None
    initial_price: float

    class Config:
        from_attributes = True


class EventOut(BaseModel):
    event_type: str
    event_level_pct: float | None = None
    event_strike_pct: float | None = None
    event_date: date
    event_amount: float | None = None
    event_payment_date: date | None = None

    class Config:
        from_attributes = True


class ProductSummary(BaseModel):
    """List view — lightweight summary per product."""

    product_isin: str
    sedol: str | None = None
    short_description: str | None = None
    issuer: str | None = None
    issue_date: date
    currency: str
    maturity: date
    product_type: str | None = None
    approved: bool
    underlying_count: int
    event_count: int


class ProductDetail(BaseModel):
    """Detail view — full product with nested underlyings and events."""

    product_isin: str
    sedol: str | None = None
    short_description: str | None = None
    issuer: str | None = None
    issue_date: date
    currency: str
    maturity: date
    product_type: str | None = None
    word_description: str | None = None
    approved: bool
    underlyings: list[UnderlyingOut]
    events: list[EventOut]


class ValidationIssueOut(BaseModel):
    field: str
    rule: str
    message: str
    severity: str


class ValidationResultOut(BaseModel):
    is_valid: bool
    issues: list[ValidationIssueOut]


class ExtractionResponse(BaseModel):
    """Full response from the upload-termsheet endpoint."""

    filename: str
    size_bytes: int
    status: str
    product_isin: str
    approved: bool
    data: dict[str, Any]
    validation: ValidationResultOut


class JobCreatedResponse(BaseModel):
    """Response from the async upload endpoint."""

    job_id: str
    filename: str
    size_bytes: int
