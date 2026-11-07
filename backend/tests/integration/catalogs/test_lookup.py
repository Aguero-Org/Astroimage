from __future__ import annotations

from astropy.coordinates import SkyCoord
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.catalogs.download import VIZIER_SOURCE
from astroimage.catalogs.lookup import CatalogLookup
from astroimage.catalogs.model import CatalogMetadata, CatalogRow, CatalogTable
from astroimage.catalogs.repository import CatalogDownloadRepository
from astroimage.catalogs.schema import CatalogRecommendationConfigSchema

_ROW_LIMIT = 50
_TABLE = CatalogTable(
    catalogue_id="I/350",
    rows=(
        CatalogRow(
            index=0,
            ra_deg=10.0,
            dec_deg=20.005556,
            separation_arcsec=20.0,
            values=(("ID", "A"),),
        ),
    ),
)


class _CountingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
    ) -> list[CatalogTable]:
        self.calls += 1
        return [_TABLE]

    def catalog_metadata(self, catalogue_id: str) -> CatalogMetadata:
        return CatalogMetadata(catalogue_id=catalogue_id)


class _Readme:
    def fetch(self, catalogue_id: str) -> None:
        return None


async def _store_covering_download(repository: CatalogDownloadRepository) -> None:
    await repository.replace(
        source=VIZIER_SOURCE,
        region_key="10.000000:20.000000:60.0:50",
        ra_deg=10.0,
        dec_deg=20.0,
        radius_arcsec=60.0,
        row_limit=_ROW_LIMIT,
        tables=[_TABLE],
    )


def _lookup(repository: CatalogDownloadRepository) -> tuple[CatalogLookup, _CountingProvider]:
    provider = _CountingProvider()
    return (
        CatalogLookup(
            provider=provider,
            readme_fetcher=_Readme(),
            query_timeout_s=1,
            downloads=repository,
        ),
        provider,
    )


async def test_covered_cone_skips_vizier(db_session: AsyncSession) -> None:
    repository = CatalogDownloadRepository(db_session, ttl_s=3600)
    await _store_covering_download(repository)
    lookup, provider = _lookup(repository)

    tables, error = await lookup.query_region(
        SkyCoord(10.0, 20.005556, unit="deg"),
        CatalogRecommendationConfigSchema(search_radius_arcsec=30.0),
    )

    assert error is None
    assert [table.catalogue_id for table in tables] == ["I/350"]
    assert provider.calls == 0


async def test_cone_outside_every_download_queries_vizier(db_session: AsyncSession) -> None:
    repository = CatalogDownloadRepository(db_session, ttl_s=3600)
    await _store_covering_download(repository)
    lookup, provider = _lookup(repository)

    tables, error = await lookup.query_region(
        SkyCoord(10.0, 20.05, unit="deg"),
        CatalogRecommendationConfigSchema(search_radius_arcsec=30.0),
    )

    assert error is None
    assert tables == [_TABLE]
    assert provider.calls == 1
