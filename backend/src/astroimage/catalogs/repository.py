from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.catalogs.download import (
    EMPTY_CATALOGUE_ID,
    CatalogDownload,
    table_from_payload,
    table_payload,
)
from astroimage.catalogs.model import CatalogTable
from astroimage.catalogs.papers import PaperMetadata, PaperRecord


class CatalogDownloadRepository:
    def __init__(self, session: AsyncSession, *, ttl_s: float) -> None:
        self._session = session
        self._ttl_s = ttl_s

    async def find_fresh(
        self,
        *,
        source: str,
        region_key: str,
        row_limit: int,
    ) -> list[CatalogTable] | None:
        statement = select(CatalogDownload).where(
            CatalogDownload.source == source,
            CatalogDownload.region_key == region_key,
            CatalogDownload.row_limit == row_limit,
        )
        result = await self._session.execute(statement)
        stored = list(result.scalars().all())
        if not stored:
            return None
        cutoff = datetime.now(UTC) - timedelta(seconds=self._ttl_s)
        if any(row.fetched_at < cutoff for row in stored):
            return None
        return [
            table_from_payload(row.catalogue_id, row.payload)
            for row in stored
            if row.catalogue_id != EMPTY_CATALOGUE_ID
        ]

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
    ) -> None:
        await self._session.execute(
            delete(CatalogDownload).where(
                CatalogDownload.source == source,
                CatalogDownload.region_key == region_key,
                CatalogDownload.row_limit == row_limit,
            )
        )
        version = uuid4().hex
        fetched_at = datetime.now(UTC)
        rows = tables or [_empty_table()]
        for table in rows:
            self._session.add(
                CatalogDownload(
                    source=source,
                    catalogue_id=table.catalogue_id,
                    region_key=region_key,
                    ra_deg=ra_deg,
                    dec_deg=dec_deg,
                    radius_arcsec=radius_arcsec,
                    row_limit=row_limit,
                    version=version,
                    fetched_at=fetched_at,
                    payload=table_payload(table),
                )
            )
        await self._session.flush()


def _empty_table() -> CatalogTable:
    return CatalogTable(catalogue_id=EMPTY_CATALOGUE_ID)


class PaperMetadataRepository:
    def __init__(self, session: AsyncSession, *, ttl_s: float) -> None:
        self._session = session
        self._ttl_s = ttl_s

    async def find_fresh(self, keys: Sequence[str]) -> dict[str, PaperRecord]:
        if not keys:
            return {}
        statement = select(PaperMetadata).where(PaperMetadata.lookup_key.in_(tuple(keys)))
        result = await self._session.execute(statement)
        cutoff = datetime.now(UTC) - timedelta(seconds=self._ttl_s)
        fresh: dict[str, PaperRecord] = {}
        for row in result.scalars().all():
            if row.fetched_at < cutoff:
                continue
            fresh[row.lookup_key] = PaperRecord(
                lookup_key=row.lookup_key,
                bibcode=row.bibcode,
                doi=row.doi,
                title=row.title,
                abstract=row.abstract,
            )
        return fresh

    async def save(self, records: Sequence[PaperRecord]) -> None:
        if not records:
            return
        keys = [record.lookup_key for record in records]
        await self._session.execute(delete(PaperMetadata).where(PaperMetadata.lookup_key.in_(keys)))
        fetched_at = datetime.now(UTC)
        for record in records:
            self._session.add(
                PaperMetadata(
                    lookup_key=record.lookup_key,
                    bibcode=record.bibcode,
                    doi=record.doi,
                    title=record.title,
                    abstract=record.abstract,
                    fetched_at=fetched_at,
                )
            )
        await self._session.flush()
