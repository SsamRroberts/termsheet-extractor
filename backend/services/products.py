"""Product queries and approval."""

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models.product import Product
from schemas.product import (
    EventOut,
    ProductDetail,
    ProductSummary,
    UnderlyingOut,
)


def approve(product_isin: str, db: Session) -> dict[str, Any]:
    """Set a product's approved flag to True."""
    product = db.query(Product).filter(Product.product_isin == product_isin).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.approved:
        raise HTTPException(status_code=409, detail="Product is already approved")

    product.approved = True
    db.flush()
    return {"product_isin": product_isin, "approved": True}


def list_all(db: Session) -> list[ProductSummary]:
    """List all extracted termsheet products."""
    products = db.query(Product).order_by(Product.issue_date.desc()).all()
    return [
        ProductSummary(
            product_isin=p.product_isin,
            sedol=p.sedol,
            short_description=p.short_description,
            issuer=p.issuer,
            issue_date=p.issue_date,
            currency=p.currency,
            maturity=p.maturity,
            product_type=p.product_type,
            approved=p.approved,
            underlying_count=len(p.underlyings),
            event_count=len(p.events),
        )
        for p in products
    ]


def get_by_isin(product_isin: str, db: Session) -> ProductDetail:
    """Get full details for a given extracted termsheet."""
    product = db.query(Product).filter(Product.product_isin == product_isin).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductDetail(
        product_isin=product.product_isin,
        sedol=product.sedol,
        short_description=product.short_description,
        issuer=product.issuer,
        issue_date=product.issue_date,
        currency=product.currency,
        maturity=product.maturity,
        product_type=product.product_type,
        word_description=product.word_description,
        approved=product.approved,
        underlyings=[UnderlyingOut.model_validate(u) for u in product.underlyings],
        events=[
            EventOut.model_validate(e)
            for e in sorted(product.events, key=lambda e: e.event_date)
        ],
    )
