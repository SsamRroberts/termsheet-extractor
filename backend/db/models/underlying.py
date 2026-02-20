from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base

if TYPE_CHECKING:
    from db.models.product import Product


class Underlying(Base):
    __tablename__ = "underlyings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_isin: Mapped[str] = mapped_column(String(12), ForeignKey("products.product_isin", ondelete="CASCADE"), nullable=False, index=True)
    bbg_code: Mapped[str] = mapped_column(String, nullable=False, comment="Bloomberg ticker e.g. SX5E INDEX")
    weight: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    initial_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False, comment="Initial fixing level")

    product: Mapped["Product"] = relationship("Product", back_populates="underlyings")
