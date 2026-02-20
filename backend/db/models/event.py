from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base

if TYPE_CHECKING:
    from db.models.product import Product


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_isin: Mapped[str] = mapped_column(String(12), ForeignKey("products.product_isin", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False, comment="Strike | Coupon | Autocall | Maturity")
    event_level_pct: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True, comment="Barrier level as percentage")
    event_strike_pct: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True, comment="Strike level as percentage")
    event_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, comment="Valuation / observation date")
    event_amount: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True, comment="Payment amount or rate")
    event_payment_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True, comment="Settlement date")

    product: Mapped["Product"] = relationship("Product", back_populates="events")
