from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base

if TYPE_CHECKING:
    from db.models.event import Event
    from db.models.extraction_metadata import ExtractionMetadata
    from db.models.underlying import Underlying


class Product(Base):
    __tablename__ = "products"

    product_isin: Mapped[str] = mapped_column(String(12), primary_key=True, comment="ISIN code")
    sedol: Mapped[str | None] = mapped_column(String(7), nullable=True)
    short_description: Mapped[str | None] = mapped_column(String, nullable=True)
    issuer: Mapped[str | None] = mapped_column(String, nullable=True)
    issue_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    maturity: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    product_type: Mapped[str | None] = mapped_column(String, nullable=True)
    word_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    events: Mapped[list["Event"]] = relationship("Event", back_populates="product", cascade="all, delete-orphan")
    underlyings: Mapped[list["Underlying"]] = relationship("Underlying", back_populates="product", cascade="all, delete-orphan")
    extraction_metadata: Mapped[list["ExtractionMetadata"]] = relationship("ExtractionMetadata", back_populates="product", cascade="all, delete-orphan")
