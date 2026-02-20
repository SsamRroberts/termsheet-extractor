"""termsheet schema

Revision ID: 001_termsheet
Revises:
Create Date: 2026-02-20 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_termsheet"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("product_isin", sa.String(12), primary_key=True),
        sa.Column("sedol", sa.String(7), nullable=True),
        sa.Column("short_description", sa.String, nullable=True),
        sa.Column("issuer", sa.String, nullable=True),
        sa.Column("issue_date", sa.Date, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("maturity", sa.Date, nullable=False),
        sa.Column("product_type", sa.String, nullable=True),
        sa.Column("word_description", sa.Text, nullable=True),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "product_isin",
            sa.String(12),
            sa.ForeignKey("products.product_isin", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("event_type", sa.String, nullable=False),
        sa.Column("event_level_pct", sa.Numeric, nullable=True),
        sa.Column("event_strike_pct", sa.Numeric, nullable=True),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("event_amount", sa.Numeric, nullable=True),
        sa.Column("event_payment_date", sa.Date, nullable=True),
    )

    op.create_table(
        "underlyings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "product_isin",
            sa.String(12),
            sa.ForeignKey("products.product_isin", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("bbg_code", sa.String, nullable=False),
        sa.Column("weight", sa.Numeric, nullable=True),
        sa.Column("initial_price", sa.Numeric, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("underlyings")
    op.drop_table("events")
    op.drop_table("products")
