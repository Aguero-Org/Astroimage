from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import ColumnElement, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from astroimage.catalogs.download import (
    EMPTY_CATALOGUE_ID,
    CatalogDownload,
    CatalogDownloadHit,
    Geography,
    table_from_payload,
    table_payload,
)
from astroimage.catalogs.model import CatalogTable
from astroimage.catalogs.papers import PaperMetadata, PaperRecord

_CONSERVATIVE_METERS_PER_ARCSEC = 6_335_439.0 * math.pi / (180.0 * 3600.0)


class CatalogDownloadRepository:
    def __init__(self, session: AsyncSession, *, ttl_s: float) -> None:
        self._session = session
        self._ttl_s = ttl_s

    async def find_fresh(
        self,
        *,
        source: str,
        region_key: str,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        row_limit: int,
        region_suffix: str | None = None,
    ) -> CatalogDownloadHit | None:
        cutoff = datetime.now(UTC) - timedelta(seconds=self._ttl_s)
        suffix = _region_suffix(region_suffix)
        exact = (
            (
                await self._session.execute(
                    select(CatalogDownload).where(
                        CatalogDownload.source == source,
                        CatalogDownload.region_key == region_key,
                        CatalogDownload.row_limit == row_limit,
                        CatalogDownload.fetched_at >= cutoff,
                        *suffix,
                    )
                )
            )
            .scalars()
            .all()
        )
        if exact:
            return CatalogDownloadHit(tables=_tables_from_rows(exact), covered=False)

        max_radius = (
            await self._session.execute(
                select(func.max(CatalogDownload.radius_arcsec)).where(
                    CatalogDownload.source == source,
                    CatalogDownload.row_limit == row_limit,
                    CatalogDownload.fetched_at >= cutoff,
                    CatalogDownload.radius_arcsec >= radius_arcsec,
                    *suffix,
                )
            )
        ).scalar_one_or_none()
        if max_radius is None:
            return None

        point = func.ST_SetSRID(func.ST_MakePoint(ra_deg, dec_deg), 4326).cast(Geography())
        limited = aliased(CatalogDownload)
        truncated = (
            select(limited.id)
            .where(
                limited.version == CatalogDownload.version,
                func.jsonb_array_length(limited.payload["rows"]) >= limited.row_limit,
            )
            .exists()
        )
        statement = (
            select(CatalogDownload.version)
            .where(
                CatalogDownload.source == source,
                CatalogDownload.row_limit == row_limit,
                CatalogDownload.fetched_at >= cutoff,
                CatalogDownload.radius_arcsec >= radius_arcsec,
                *suffix,
                ~truncated,
                func.ST_DWithin(
                    CatalogDownload.center,
                    point,
                    (max_radius - radius_arcsec) * _CONSERVATIVE_METERS_PER_ARCSEC,
                ),
                func.ST_DWithin(
                    CatalogDownload.center,
                    point,
                    (CatalogDownload.radius_arcsec - radius_arcsec)
                    * _CONSERVATIVE_METERS_PER_ARCSEC,
                ),
            )
            .order_by(CatalogDownload.radius_arcsec, CatalogDownload.fetched_at.desc())
            .limit(1)
        )
        version = (await self._session.execute(statement)).scalar_one_or_none()
        if version is None:
            return None
        stored = (
            (
                await self._session.execute(
                    select(CatalogDownload).where(
                        CatalogDownload.source == source,
                        CatalogDownload.version == version,
                    )
                )
            )
            .scalars()
            .all()
        )
        return CatalogDownloadHit(tables=_tables_from_rows(stored), covered=True)

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


def _region_suffix(region_suffix: str | None) -> tuple[ColumnElement[bool], ...]:
    if region_suffix is None:
        return ()
    return (func.right(CatalogDownload.region_key, len(region_suffix)) == region_suffix,)


def _tables_from_rows(rows: Sequence[CatalogDownload]) -> list[CatalogTable]:
    return [
        table_from_payload(row.catalogue_id, row.payload)
        for row in rows
        if row.catalogue_id != EMPTY_CATALOGUE_ID
    ]


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
