from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Index, Integer, String, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from astroimage.catalogs.model import CatalogRow, CatalogTable
from astroimage.shared.database import Base

VIZIER_SOURCE = "vizier"
EMPTY_CATALOGUE_ID = ""


class CatalogDownload(Base):
    __tablename__ = "catalog_downloads"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "catalogue_id",
            "region_key",
            "row_limit",
            name="uq_catalog_downloads_region",
        ),
        Index("ix_catalog_downloads_region_lookup", "source", "region_key", "row_limit"),
        Index("ix_catalog_downloads_fetched_at", "fetched_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    catalogue_id: Mapped[str] = mapped_column(String(128), nullable=False)
    region_key: Mapped[str] = mapped_column(String(160), nullable=False)
    ra_deg: Mapped[float] = mapped_column(Float, nullable=False)
    dec_deg: Mapped[float] = mapped_column(Float, nullable=False)
    radius_arcsec: Mapped[float] = mapped_column(Float, nullable=False)
    row_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


def table_payload(table: CatalogTable) -> dict[str, Any]:
    return {
        "column_names": list(table.column_names),
        "rows": [
            {
                "index": row.index,
                "ra_deg": row.ra_deg,
                "dec_deg": row.dec_deg,
                "separation_arcsec": row.separation_arcsec,
                "values": [list(pair) for pair in row.values],
            }
            for row in table.rows
        ],
    }


def table_from_payload(catalogue_id: str, payload: dict[str, Any]) -> CatalogTable:
    raw_rows = payload.get("rows", [])
    rows = tuple(
        CatalogRow(
            index=int(row["index"]),
            ra_deg=row.get("ra_deg"),
            dec_deg=row.get("dec_deg"),
            separation_arcsec=row.get("separation_arcsec"),
            values=tuple((str(name), str(value)) for name, value in row.get("values", [])),
        )
        for row in raw_rows
    )
    column_names = tuple(str(name) for name in payload.get("column_names", []))
    return CatalogTable(catalogue_id=catalogue_id, column_names=column_names, rows=rows)


class CatalogDownloadStore(Protocol):
    async def find_fresh(
        self,
        *,
        source: str,
        region_key: str,
        row_limit: int,
    ) -> list[CatalogTable] | None: ...

    async def replace(
        self,
        *,
        source: str,
        region_key: str,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        row_limit: int,
        tables: list[CatalogTable],
    ) -> None: ...
