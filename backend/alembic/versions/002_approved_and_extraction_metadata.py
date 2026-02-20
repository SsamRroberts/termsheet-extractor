"""approved column and extraction metadata blob_path

Revision ID: 002_approved_meta
Revises: 001_termsheet
Create Date: 2026-02-20 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_approved_meta"
down_revision: Union[str, None] = "001_termsheet"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "approved",
            sa.Boolean,
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.create_table(
        "extraction_metadata",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "product_isin",
            sa.String(12),
            sa.ForeignKey("products.product_isin", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("source_filename", sa.String, nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("blob_path", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("extraction_metadata")
    op.drop_column("products", "approved")
