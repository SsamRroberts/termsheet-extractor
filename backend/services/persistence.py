"""Transactional DB write for extracted termsheet data."""

import datetime

from sqlalchemy.orm import Session

from db.models.event import Event
from db.models.extraction_metadata import ExtractionMetadata
from db.models.product import Product
from db.models.underlying import Underlying
from services.termsheet_llm import TermsheetData


def persist_extraction(
    data: TermsheetData,
    source_filename: str,
    blob_path: str,
    status: str,
    db: Session,
) -> Product:
    """Create Product with child Events, Underlyings, and ExtractionMetadata.

    Uses db.flush() so the caller (get_db dependency) handles commit/rollback.
    """
    p = data.product
    product = Product(
        product_isin=p.product_isin,
        sedol=p.sedol,
        short_description=p.short_description,
        issuer=p.issuer,
        issue_date=p.issue_date,
        currency=p.currency,
        maturity=p.maturity,
        product_type=p.product_type,
        word_description=p.word_description,
        approved=False,
    )
    db.add(product)

    for u in data.underlyings:
        db.add(Underlying(
            product_isin=p.product_isin,
            bbg_code=u.bbg_code,
            weight=u.weight,
            initial_price=u.initial_price,
        ))

    for e in data.events:
        db.add(Event(
            product_isin=p.product_isin,
            event_type=e.event_type,
            event_level_pct=e.event_level_pct,
            event_strike_pct=e.event_strike_pct,
            event_date=e.event_date,
            event_amount=e.event_amount,
            event_payment_date=e.event_payment_date,
        ))

    db.add(ExtractionMetadata(
        product_isin=p.product_isin,
        source_filename=source_filename,
        extracted_at=datetime.datetime.now(datetime.timezone.utc),
        status=status,
        blob_path=blob_path,
    ))

    db.flush()
    return product
