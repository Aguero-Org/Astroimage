"""create image_transfers table

Revision ID: 20260929_0002
Revises: 20260830_0001
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260929_0002"
down_revision: str | None = "20260830_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "image_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("destination", sa.String(length=32), nullable=False),
        sa.Column("target_name", sa.String(length=256), nullable=False),
        sa.Column("data_uri", sa.String(length=1024), nullable=False),
        sa.Column("product_filename", sa.String(length=512), nullable=False),
        sa.Column("observation_id", sa.String(length=128), nullable=False),
        sa.Column("proposal_id", sa.String(length=128), nullable=False),
        sa.Column("instrument", sa.String(length=128), nullable=True),
        sa.Column("filters", sa.String(length=256), nullable=True),
        sa.Column("observed_at", sa.String(length=64), nullable=True),
        sa.Column("ra_deg", sa.Float(), nullable=False),
        sa.Column("dec_deg", sa.Float(), nullable=False),
        sa.Column("bytes_transferred", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_bytes", sa.BigInteger(), nullable=True),
        sa.Column("etag", sa.String(length=256), nullable=True),
        sa.Column("last_modified", sa.String(length=128), nullable=True),
        sa.Column("speed_bytes_per_second", sa.Float(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("slug", sa.String(length=512), nullable=True),
        sa.Column("samples", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_image_transfers_data_uri", "image_transfers", ["data_uri"])
    op.create_index("ix_image_transfers_status", "image_transfers", ["status"])


def downgrade() -> None:
    op.drop_index("ix_image_transfers_status", table_name="image_transfers")
    op.drop_index("ix_image_transfers_data_uri", table_name="image_transfers")
    op.drop_table("image_transfers")
