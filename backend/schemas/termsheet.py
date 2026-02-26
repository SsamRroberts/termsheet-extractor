"""Pydantic models for LLM structured output (mirror DB schema)."""

from datetime import date

from pydantic import BaseModel, Field


class Underlying(BaseModel):
    bbg_code: str = Field(description="Bloomberg ticker code, e.g. 'SX5E INDEX'")
    weight: float | None = Field(None, description="Portfolio weight as a decimal (e.g. 0.5 for 50%)")
    initial_price: float = Field(description="RI Initial Value / starting price for the underlying")


class Event(BaseModel):
    event_type: str = Field(
        description=(
            "One of: 'strike', 'coupon', 'auto_early_redemption', 'knock_in'"
        )
    )
    event_level_pct: float | None = Field(
        None,
        description="Barrier or trigger level as a percentage (e.g. 75.0 for 75%)",
    )
    event_strike_pct: float | None = Field(
        None,
        description="Strike percentage if applicable (e.g. 100.0 for 100%)",
    )
    event_date: date = Field(description="Valuation date for this event (YYYY-MM-DD)")
    event_amount: float | None = Field(
        None,
        description="Payment amount or rate as a percentage (e.g. 2.0375 for 2.0375%)",
    )
    event_payment_date: date | None = Field(
        None,
        description="Payment/settlement date if different from event_date (YYYY-MM-DD)",
    )


class Product(BaseModel):
    product_isin: str = Field(description="12-character ISIN code, e.g. 'XS3184638594'")
    sedol: str | None = Field(None, description="7-character SEDOL code")
    short_description: str | None = Field(None, description="Product title from the document heading")
    issuer: str | None = Field(None, description="Short issuer name, e.g. 'BBVA' not the full legal entity")
    issue_date: date = Field(description="Issue date (YYYY-MM-DD)")
    currency: str = Field(description="3-letter ISO currency code, e.g. 'GBP'")
    maturity: date = Field(description="Maturity date (YYYY-MM-DD)")
    product_type: str | None = Field(None, description="Product category, e.g. 'Phoenix Autocall', 'Reverse Convertible'")
    word_description: str | None = Field(
        None,
        description="Full text description of the product from the termsheet header",
    )


class TermsheetData(BaseModel):
    """Complete structured extraction from a termsheet PDF."""

    product: Product
    underlyings: list[Underlying]
    events: list[Event]
