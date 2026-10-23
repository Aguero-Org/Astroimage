"""widen paper_metadata.bibcode

Revision ID: 20261023_0006
Revises: 20261023_0005
Create Date: 2026-10-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261023_0006"
down_revision: str | None = "20261023_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "paper_metadata",
        "bibcode",
        existing_type=sa.String(length=32),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "paper_metadata",
        "bibcode",
        existing_type=sa.Text(),
        type_=sa.String(length=32),
        existing_nullable=True,
    )
