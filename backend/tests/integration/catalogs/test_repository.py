from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.catalogs.download import (
    VIZIER_SOURCE,
    CatalogDownload,
    CatalogDownloadHit,
)
from astroimage.catalogs.model import CatalogRow, CatalogTable
from astroimage.catalogs.papers import PaperRecord
from astroimage.catalogs.repository import CatalogDownloadRepository, PaperMetadataRepository

_KEY = "10.000000:20.000000:30.0:50"
_COVERED_KEY = "10.000000:20.005556:30.0:50"
_ROW_LIMIT = 50


def _table(rows: int = 1) -> CatalogTable:
    return CatalogTable(
        catalogue_id="I/350",
        column_names=("ID",),
        rows=tuple(
            CatalogRow(index=index, ra_deg=10.0, dec_deg=20.0, values=(("ID", str(index)),))
            for index in range(rows)
        ),
    )


@pytest.fixture
def repository(db_session: AsyncSession) -> CatalogDownloadRepository:
    return CatalogDownloadRepository(db_session, ttl_s=3600)


async def _find(
    repository: CatalogDownloadRepository,
    *,
    region_key: str = _KEY,
    ra_deg: float = 10.0,
    dec_deg: float = 20.0,
    radius_arcsec: float = 30.0,
    row_limit: int = _ROW_LIMIT,
) -> CatalogDownloadHit | None:
    return await repository.find_fresh(
        source=VIZIER_SOURCE,
        region_key=region_key,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        radius_arcsec=radius_arcsec,
        row_limit=row_limit,
    )


async def test_replace_and_find_fresh(repository: CatalogDownloadRepository) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=30.0,
        row_limit=_ROW_LIMIT,
        tables=[_table()],
    )

    hit = await _find(repository)

    assert hit is not None
    assert hit.tables == [_table()]
    assert hit.covered is False


async def test_empty_download_is_a_hit(repository: CatalogDownloadRepository) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=30.0,
        row_limit=_ROW_LIMIT,
        tables=[],
    )

    hit = await _find(repository)

    assert hit is not None
    assert hit.tables == []


async def test_covered_cone_reuses_a_fresh_download(
    repository: CatalogDownloadRepository,
) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=60.0,
        row_limit=_ROW_LIMIT,
        tables=[_table()],
    )

    hit = await _find(
        repository,
        region_key=_COVERED_KEY,
        dec_deg=20.005556,
        radius_arcsec=30.0,
    )

    assert hit is not None
    assert hit.tables == [_table()]
    assert hit.covered is True


async def test_covered_empty_download_is_a_hit(repository: CatalogDownloadRepository) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=60.0,
        row_limit=_ROW_LIMIT,
        tables=[],
    )

    hit = await _find(repository, region_key=_COVERED_KEY, dec_deg=20.005556, radius_arcsec=30.0)

    assert hit is not None
    assert hit.tables == []


async def test_partial_overlap_is_a_miss(repository: CatalogDownloadRepository) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=60.0,
        row_limit=_ROW_LIMIT,
        tables=[_table()],
    )

    stored = await _find(
        repository,
        region_key="10.000000:20.008333:60.0:50",
        dec_deg=20.008333,
        radius_arcsec=60.0,
    )

    assert stored is None


async def test_cone_outside_every_download_is_a_miss(
    repository: CatalogDownloadRepository,
) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=60.0,
        row_limit=_ROW_LIMIT,
        tables=[_table()],
    )

    stored = await _find(
        repository,
        region_key="10.000000:20.033333:30.0:50",
        dec_deg=20.033333,
        radius_arcsec=30.0,
    )

    assert stored is None


async def test_region_suffix_does_not_reuse_another_label(
    repository: CatalogDownloadRepository,
) -> None:
    await repository.replace(
        source="simbad",
        region_key="10.000000:20.000000:60.0:25:type=*",
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=60.0,
        row_limit=25,
        tables=[_table()],
    )

    other_type = await repository.find_fresh(
        source="simbad",
        region_key="10.000000:20.000000:30.0:25:type=SNR",
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=30.0,
        row_limit=25,
        region_suffix=":type=SNR",
    )
    same_type = await repository.find_fresh(
        source="simbad",
        region_key="10.000000:20.000000:30.0:25:type=*",
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=30.0,
        row_limit=25,
        region_suffix=":type=*",
    )

    assert other_type is None
    assert same_type is not None
    assert same_type.covered is True


async def test_covered_cone_with_another_row_limit_is_a_miss(
    repository: CatalogDownloadRepository,
) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=60.0,
        row_limit=_ROW_LIMIT,
        tables=[_table()],
    )

    stored = await _find(
        repository,
        region_key=_COVERED_KEY,
        dec_deg=20.005556,
        radius_arcsec=30.0,
        row_limit=20,
    )

    assert stored is None


async def test_stale_covered_cone_is_a_miss(
    repository: CatalogDownloadRepository,
    db_session: AsyncSession,
) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=60.0,
        row_limit=_ROW_LIMIT,
        tables=[_table()],
    )
    stored_row = (await db_session.execute(select(CatalogDownload))).scalars().first()
    assert stored_row is not None
    stored_row.fetched_at = datetime.now(UTC) - timedelta(hours=2)
    await db_session.flush()

    stored = await _find(repository, region_key=_COVERED_KEY, dec_deg=20.005556, radius_arcsec=30.0)

    assert stored is None


async def test_truncated_download_serves_only_its_region(
    repository: CatalogDownloadRepository,
) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key=_KEY,
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=60.0,
        row_limit=_ROW_LIMIT,
        tables=[_table(rows=_ROW_LIMIT)],
    )

    exact = await _find(repository)
    covered = await _find(
        repository, region_key=_COVERED_KEY, dec_deg=20.005556, radius_arcsec=30.0
    )

    assert exact is not None
    assert exact.tables == [_table(rows=_ROW_LIMIT)]
    assert exact.covered is False
    assert covered is None


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
        row_limit=_ROW_LIMIT,
        tables=[_table()],
    )
    stored_row = (await db_session.execute(select(CatalogDownload))).scalars().first()
    assert stored_row is not None
    stored_row.fetched_at = datetime.now(UTC) - timedelta(hours=2)
    await db_session.flush()

    assert await _find(repository) is None


async def test_paper_metadata_roundtrip(db_session: AsyncSession) -> None:
    repository = PaperMetadataRepository(db_session, ttl_s=3600)
    record = PaperRecord(
        lookup_key="2016A&A...595A...1G",
        bibcode="2016A&A...595A...1G",
        doi="10.1051/0004-6361/201629272",
        title="Gaia Data Release 1",
        abstract="Positions and photometry.",
    )

    await repository.save([record])
    fresh = await repository.find_fresh([record.lookup_key, "missing"])

    assert fresh == {record.lookup_key: record}


async def test_paper_metadata_accepts_a_long_bibcode(db_session: AsyncSession) -> None:
    repository = PaperMetadataRepository(db_session, ttl_s=3600)
    bibcode = "ROSAT News 72, 25-May-2000 (2000"
    record = PaperRecord(lookup_key=bibcode, bibcode=bibcode, title="ROSAT")

    await repository.save([record])
    fresh = await repository.find_fresh([bibcode])

    assert fresh[bibcode].title == "ROSAT"
