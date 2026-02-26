"""Business-rule validation for extracted termsheet data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy.orm import Session

from db.models.product import Product
from schemas.termsheet import TermsheetData


@dataclass
class ValidationIssue:
    field: str
    rule: str
    message: str
    severity: Literal["error", "warning"]


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "issues": [
                {"field": i.field, "rule": i.rule, "message": i.message, "severity": i.severity}
                for i in self.issues
            ],
        }


def _check_isin_format(isin: str) -> bool:
    return bool(re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", isin))


def _check_isin_luhn(isin: str) -> bool:
    """Validate ISIN check digit using Luhn algorithm on letter-expanded digits."""
    digits = ""
    for ch in isin:
        if ch.isdigit():
            digits += ch
        else:
            digits += str(ord(ch) - ord("A") + 10)

    # Standard Luhn on the digit string
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def validate_termsheet(data: TermsheetData, db: Session) -> ValidationResult:
    """Run all business-rule checks against extracted data."""
    result = ValidationResult()
    product = data.product

    # isin_format
    if not _check_isin_format(product.product_isin):
        result.issues.append(ValidationIssue(
            field="product_isin", rule="isin_format",
            message=f"ISIN '{product.product_isin}' does not match expected format (2 letters + 9 alphanumeric + 1 digit)",
            severity="error",
        ))

    # isin_luhn
    if _check_isin_format(product.product_isin) and not _check_isin_luhn(product.product_isin):
        result.issues.append(ValidationIssue(
            field="product_isin", rule="isin_luhn",
            message=f"ISIN '{product.product_isin}' fails Luhn checksum validation",
            severity="error",
        ))

    # issue_before_maturity
    if product.issue_date >= product.maturity:
        result.issues.append(ValidationIssue(
            field="issue_date", rule="issue_before_maturity",
            message=f"Issue date ({product.issue_date}) must be before maturity ({product.maturity})",
            severity="error",
        ))

    # min_underlyings
    if len(data.underlyings) < 1:
        result.issues.append(ValidationIssue(
            field="underlyings", rule="min_underlyings",
            message="At least one underlying is required",
            severity="error",
        ))

    # barrier_range — check coupon and knock_in event_level_pct
    for i, event in enumerate(data.events):
        if event.event_type in ("coupon", "knock_in") and event.event_level_pct is not None:
            if not (0 <= event.event_level_pct <= 100):
                result.issues.append(ValidationIssue(
                    field=f"events[{i}].event_level_pct", rule="barrier_range",
                    message=f"Event level {event.event_level_pct}% is outside 0-100 range",
                    severity="error",
                ))

    # duplicate_isin
    existing = db.query(Product).filter_by(product_isin=product.product_isin).first()
    if existing:
        result.issues.append(ValidationIssue(
            field="product_isin", rule="duplicate_isin",
            message=f"Product with ISIN '{product.product_isin}' already exists in the database",
            severity="error",
        ))

    # event_within_lifetime (warning)
    for i, event in enumerate(data.events):
        if event.event_date < product.issue_date or event.event_date > product.maturity:
            result.issues.append(ValidationIssue(
                field=f"events[{i}].event_date", rule="event_within_lifetime",
                message=f"Event date {event.event_date} is outside product lifetime ({product.issue_date} to {product.maturity})",
                severity="warning",
            ))

    return result
