"""create paper_metadata table

Revision ID: 20261023_0005
Revises: 20261021_0004
Create Date: 2026-10-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261023_0005"
down_revision: str | None = "20261021_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "paper_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("lookup_key", sa.String(length=256), nullable=False),
        sa.Column("bibcode", sa.String(length=32), nullable=True),
        sa.Column("doi", sa.String(length=256), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("lookup_key", name="uq_paper_metadata_lookup_key"),
    )


def downgrade() -> None:
    op.drop_table("paper_metadata")
