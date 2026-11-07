"""add PostGIS coverage to catalog downloads

Revision ID: 20261106_0009
Revises: 20261027_0008
Create Date: 2026-11-06
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261106_0009"
down_revision: str | None = "20261027_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute(
        "ALTER TABLE catalog_downloads "
        "ADD COLUMN center geography(Point, 4326) "
        "GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(ra_deg, dec_deg), 4326)::geography) "
        "STORED"
    )
    op.execute("ALTER TABLE catalog_downloads ALTER COLUMN center SET NOT NULL")
    op.create_index(
        "ix_catalog_downloads_center_gist",
        "catalog_downloads",
        ["center"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index("ix_catalog_downloads_center_gist", table_name="catalog_downloads")
    op.drop_column("catalog_downloads", "center")
