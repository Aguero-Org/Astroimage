"""create catalog_downloads table

Revision ID: 20261021_0004
Revises: 20260929_0003
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261021_0004"
down_revision: str | None = "20260929_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "catalog_downloads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("catalogue_id", sa.String(length=128), nullable=False),
        sa.Column("region_key", sa.String(length=160), nullable=False),
        sa.Column("ra_deg", sa.Float(), nullable=False),
        sa.Column("dec_deg", sa.Float(), nullable=False),
        sa.Column("radius_arcsec", sa.Float(), nullable=False),
        sa.Column("row_limit", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.UniqueConstraint(
            "source",
            "catalogue_id",
            "region_key",
            "row_limit",
            name="uq_catalog_downloads_region",
        ),
    )
    op.create_index(
        "ix_catalog_downloads_region_lookup",
        "catalog_downloads",
        ["source", "region_key", "row_limit"],
    )
    op.create_index(
        "ix_catalog_downloads_fetched_at",
        "catalog_downloads",
        ["fetched_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_catalog_downloads_fetched_at", table_name="catalog_downloads")
    op.drop_index("ix_catalog_downloads_region_lookup", table_name="catalog_downloads")
    op.drop_table("catalog_downloads")
