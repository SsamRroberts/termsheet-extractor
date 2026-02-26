"""Product query and approval endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.db import get_db
from schemas.product import ProductDetail, ProductSummary
from services import products

router = APIRouter()


@router.patch("/products/{product_isin}/approve")
def approve_product(product_isin: str, db: Session = Depends(get_db)):
    """Set a product's approved flag to True."""
    return products.approve(product_isin, db)


@router.get("/products", response_model=list[ProductSummary])
def list_products(db: Session = Depends(get_db)):
    """List all extracted termsheet products."""
    return products.list_all(db)


@router.get("/products/{product_isin}", response_model=ProductDetail)
def get_product(product_isin: str, db: Session = Depends(get_db)):
    """Get full details for a given extracted termsheet."""
    return products.get_by_isin(product_isin, db)
