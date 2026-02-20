from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base

if TYPE_CHECKING:
    from db.models.product import Product


class ExtractionMetadata(Base):
    """Tracks each PDF extraction run — source file, timestamps, status."""

    __tablename__ = "extraction_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_isin: Mapped[str] = mapped_column(String(12), ForeignKey("products.product_isin", ondelete="CASCADE"), nullable=False, index=True)
    source_filename: Mapped[str] = mapped_column(String, nullable=False, comment="Original PDF filename")
    extracted_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, comment="success | failed | pending_review")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Error details if extraction failed")
    blob_path: Mapped[str | None] = mapped_column(String, nullable=True, comment="Relative path to saved markdown blob")

    product: Mapped["Product"] = relationship("Product", back_populates="extraction_metadata")
