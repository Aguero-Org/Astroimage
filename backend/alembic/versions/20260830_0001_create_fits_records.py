"""create fits_records table

Revision ID: 20260830_0001
Revises:
Create Date: 2026-08-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260830_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fits_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("metadata_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.UniqueConstraint("object_key"),
    )


def downgrade() -> None:
    op.drop_table("fits_records")
