"""add content hash and source url to fits records

Revision ID: 20261027_0007
Revises: 20261023_0006
Create Date: 2026-10-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261027_0007"
down_revision: str | None = "20261023_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("fits_records", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("fits_records", sa.Column("source_url", sa.Text(), nullable=True))
    op.create_unique_constraint(
        "uq_fits_records_content_hash",
        "fits_records",
        ["content_hash"],
    )
    op.create_unique_constraint(
        "uq_fits_records_source_url",
        "fits_records",
        ["source_url"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_fits_records_source_url", "fits_records", type_="unique")
    op.drop_constraint("uq_fits_records_content_hash", "fits_records", type_="unique")
    op.drop_column("fits_records", "source_url")
    op.drop_column("fits_records", "content_hash")
