from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import astropy.units as u
from astropy.coordinates import SkyCoord

from astroimage.catalogs.cone import narrow_to_cone
from astroimage.catalogs.download import CatalogDownloadStore
from astroimage.catalogs.model import CatalogRow, CatalogTable


@dataclass(frozen=True)
class StoredConeRow:
    index: int
    ra_deg: float | None = None
    dec_deg: float | None = None
    separation_arcsec: float | None = None
    values: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class StoredConeTable:
    catalogue_id: str
    rows: tuple[StoredConeRow, ...] = ()


@dataclass(frozen=True)
class StoredCone:
    tables: tuple[StoredConeTable, ...]
    covered: bool


class ConeCache(Protocol):
    async def find(
        self,
        *,
        source: str,
        region_key: str,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        row_limit: int,
        region_suffix: str | None = None,
    ) -> StoredCone | None: ...

    async def save(
        self,
        *,
        source: str,
        region_key: str,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        row_limit: int,
        tables: tuple[StoredConeTable, ...],
    ) -> None: ...


class CatalogConeCache:
    def __init__(self, store: CatalogDownloadStore) -> None:
        self._store = store

    async def find(
        self,
        *,
        source: str,
        region_key: str,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        row_limit: int,
        region_suffix: str | None = None,
    ) -> StoredCone | None:
        hit = await self._store.find_fresh(
            source=source,
            region_key=region_key,
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            radius_arcsec=radius_arcsec,
            row_limit=row_limit,
            region_suffix=region_suffix,
        )
        if hit is None:
            return None
        tables = hit.tables
        if hit.covered:
            tables = narrow_to_cone(
                tables,
                SkyCoord(ra_deg, dec_deg, unit=u.deg, frame="icrs"),
                radius_arcsec,
            )
        return StoredCone(
            tables=tuple(_stored_table(table) for table in tables),
            covered=hit.covered,
        )

    async def save(
        self,
        *,
        source: str,
        region_key: str,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        row_limit: int,
        tables: tuple[StoredConeTable, ...],
    ) -> None:
        await self._store.replace(
            source=source,
            region_key=region_key,
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            radius_arcsec=radius_arcsec,
            row_limit=row_limit,
            tables=[_catalog_table(table) for table in tables],
        )


def _stored_table(table: CatalogTable) -> StoredConeTable:
    return StoredConeTable(
        catalogue_id=table.catalogue_id,
        rows=tuple(
            StoredConeRow(
                index=row.index,
                ra_deg=row.ra_deg,
                dec_deg=row.dec_deg,
                separation_arcsec=row.separation_arcsec,
                values=row.values,
            )
            for row in table.rows
        ),
    )


def _catalog_table(table: StoredConeTable) -> CatalogTable:
    return CatalogTable(
        catalogue_id=table.catalogue_id,
        rows=tuple(
            CatalogRow(
                index=row.index,
                ra_deg=row.ra_deg,
                dec_deg=row.dec_deg,
                separation_arcsec=row.separation_arcsec,
                values=row.values,
            )
            for row in table.rows
        ),
    )
