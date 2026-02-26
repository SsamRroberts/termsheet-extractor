"""Synthetic data factories for building test TermsheetData without Excel/LLM."""

from datetime import date
from unittest.mock import MagicMock

from schemas.termsheet import Event, Product, TermsheetData, Underlying


def make_product(**overrides) -> Product:
    """Build a valid Product with sensible defaults; override any field via kwargs."""
    defaults = dict(
        product_isin="XS3184638594",
        sedol="BVVJPF2",
        short_description="Test Product",
        issuer="BBVA",
        issue_date=date(2026, 2, 2),
        currency="GBP",
        maturity=date(2032, 2, 2),
        product_type="Phoenix Autocall",
    )
    defaults.update(overrides)
    return Product(**defaults)


def make_underlying(**overrides) -> Underlying:
    """Build a valid Underlying with sensible defaults."""
    defaults = dict(bbg_code="UKX Index", weight=None, initial_price=10148.85)
    defaults.update(overrides)
    return Underlying(**defaults)


def make_event(**overrides) -> Event:
    """Build a valid coupon Event with sensible defaults."""
    defaults = dict(
        event_type="coupon",
        event_level_pct=75.0,
        event_strike_pct=None,
        event_date=date(2026, 7, 27),
        event_amount=2.0375,
        event_payment_date=date(2026, 8, 4),
    )
    defaults.update(overrides)
    return Event(**defaults)


def make_termsheet(**overrides) -> TermsheetData:
    """Build a valid TermsheetData; override product/underlyings/events via kwargs."""
    return TermsheetData(
        product=overrides.get("product", make_product()),
        underlyings=overrides.get("underlyings", [make_underlying()]),
        events=overrides.get("events", [make_event()]),
    )


def mock_db(existing_product=None) -> MagicMock:
    """Build a mock SQLAlchemy Session, optionally with an existing product."""
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = existing_product
    return db
