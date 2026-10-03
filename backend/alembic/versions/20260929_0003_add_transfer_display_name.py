"""add display_name to image_transfers

Revision ID: 20260929_0003
Revises: 20260929_0002
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260929_0003"
down_revision: str | None = "20260929_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "image_transfers",
        sa.Column("display_name", sa.String(length=256), nullable=False, server_default=""),
    )
    op.alter_column("image_transfers", "display_name", server_default=None)


def downgrade() -> None:
    op.drop_column("image_transfers", "display_name")
