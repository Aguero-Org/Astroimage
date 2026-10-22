from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.catalogs.download import VIZIER_SOURCE, CatalogDownload
from astroimage.catalogs.model import CatalogRow, CatalogTable
from astroimage.catalogs.repository import CatalogDownloadRepository

_KEY = "10.000000:20.000000:30.0:50"


def _table() -> CatalogTable:
    return CatalogTable(
        catalogue_id="I/350",
        column_names=("ID",),
        rows=(CatalogRow(index=0, ra_deg=10.0, dec_deg=20.0, values=(("ID", "A"),)),),
    )


@pytest.fixture
def repository(db_session: AsyncSession) -> CatalogDownloadRepository:
    return CatalogDownloadRepository(db_session, ttl_s=3600)


async def test_replace_and_find_fresh(repository: CatalogDownloadRepository) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=30.0,
        row_limit=50,
        tables=[_table()],
    )

    stored = await repository.find_fresh(source=VIZIER_SOURCE, region_key=_KEY, row_limit=50)

    assert stored == [_table()]


async def test_empty_download_is_a_hit(repository: CatalogDownloadRepository) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=30.0,
        row_limit=50,
        tables=[],
    )

    stored = await repository.find_fresh(source=VIZIER_SOURCE, region_key=_KEY, row_limit=50)

    assert stored == []


async def test_stale_download_is_a_miss(
    repository: CatalogDownloadRepository,
    db_session: AsyncSession,
) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=30.0,
        row_limit=50,
        tables=[_table()],
    )
    stored_row = (await db_session.execute(select(CatalogDownload))).scalars().first()
    assert stored_row is not None
    stored_row.fetched_at = datetime.now(UTC) - timedelta(hours=2)
    await db_session.flush()

    missed = await repository.find_fresh(source=VIZIER_SOURCE, region_key=_KEY, row_limit=50)

    assert missed is None
