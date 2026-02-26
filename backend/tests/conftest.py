"""Shared fixtures: load Excel reference data into TermsheetData objects."""

import os
import sys
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock

import openpyxl
import pytest

# Allow imports from the backend package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas.termsheet import Event, Product, TermsheetData, Underlying

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
EXCEL_PATH = DATA_DIR / "XS3184638594_data tables.xlsx"
MARKDOWN_PATH = DATA_DIR / "XS3184638594_Termsheet_Final.md"

# Excel uses these event type names; the LLM schema uses different ones.
# This mapping converts Excel → LLM-schema naming.
EVENT_TYPE_MAP = {
    "Strike": "strike",
    "Coupon": "coupon",
    "Autocall": "auto_early_redemption",
    "Maturity": "knock_in",
}


def _to_date(val) -> date:
    """Convert an Excel cell value (datetime or date) to a date."""
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    raise TypeError(f"Cannot convert {val!r} to date")


def _load_sheet_rows(wb: openpyxl.Workbook, sheet_name: str) -> list[dict]:
    """Load a sheet into a list of dicts keyed by header row."""
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    headers = [h for h in rows[0] if h is not None]
    result = []
    for row in rows[1:]:
        # Only take as many values as we have headers (skip empty trailing cols)
        result.append(dict(zip(headers, row[: len(headers)])))
    return result


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def excel_workbook() -> openpyxl.Workbook:
    assert EXCEL_PATH.exists(), f"Excel file not found: {EXCEL_PATH}"
    return openpyxl.load_workbook(EXCEL_PATH, data_only=True)


@pytest.fixture(scope="session")
def excel_product_row(excel_workbook) -> dict:
    """Raw product dict straight from the Excel."""
    rows = _load_sheet_rows(excel_workbook, "XS3184638594_products")
    assert len(rows) == 1
    return rows[0]


@pytest.fixture(scope="session")
def excel_underlying_rows(excel_workbook) -> list[dict]:
    return _load_sheet_rows(excel_workbook, "XS3184638594_underlyings")


@pytest.fixture(scope="session")
def excel_event_rows(excel_workbook) -> list[dict]:
    return _load_sheet_rows(excel_workbook, "XS3184638594_events")


@pytest.fixture(scope="session")
def excel_product(excel_product_row) -> Product:
    """Excel product data as a Pydantic Product model."""
    r = excel_product_row
    return Product(
        product_isin=r["product_isin"],
        sedol=r["sedol"],
        short_description=r["short_description"],
        issuer=r["issuer"],
        issue_date=_to_date(r["issue_date"]),
        currency=r["currency"],
        maturity=_to_date(r["maturity"]),
        product_type=r["product_type"],
        word_description=r.get("word_description"),
    )


@pytest.fixture(scope="session")
def excel_underlyings(excel_underlying_rows) -> list[Underlying]:
    """Excel underlyings as Pydantic Underlying models."""
    return [
        Underlying(
            bbg_code=r["bbg_code"],
            weight=r["weight"],
            initial_price=r["initial_price"],
        )
        for r in excel_underlying_rows
    ]


@pytest.fixture(scope="session")
def excel_events(excel_event_rows) -> list[Event]:
    """Excel events as Pydantic Event models (with mapped event_type names)."""
    events = []
    for r in excel_event_rows:
        raw_type = r["event_type"]
        events.append(Event(
            event_type=EVENT_TYPE_MAP.get(raw_type, raw_type.lower()),
            event_level_pct=r.get("event_level_pct"),
            event_strike_pct=r.get("event_strike_pct"),
            event_date=_to_date(r["event_date"]),
            event_amount=r.get("event_amount"),
            event_payment_date=_to_date(r["event_payment_date"]) if r.get("event_payment_date") else None,
        ))
    return events


@pytest.fixture(scope="session")
def excel_termsheet(excel_product, excel_underlyings, excel_events) -> TermsheetData:
    """Complete TermsheetData built from the Excel reference data."""
    return TermsheetData(
        product=excel_product,
        underlyings=excel_underlyings,
        events=excel_events,
    )


@pytest.fixture()
def mock_db_session() -> MagicMock:
    """A mock SQLAlchemy Session with no existing products."""
    session = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = None
    return session


@pytest.fixture(scope="session")
def markdown_text() -> str | None:
    """Load the extracted markdown if it exists (for integration tests)."""
    if MARKDOWN_PATH.exists():
        return MARKDOWN_PATH.read_text()
    return None
