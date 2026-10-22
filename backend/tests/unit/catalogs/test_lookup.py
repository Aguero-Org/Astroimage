from __future__ import annotations

from astropy.coordinates import SkyCoord

from astroimage.catalogs.download import table_from_payload, table_payload
from astroimage.catalogs.lookup import CatalogLookup
from astroimage.catalogs.model import CatalogRow, CatalogTable
from astroimage.catalogs.region import region_key
from astroimage.catalogs.schema import CatalogRecommendationConfigSchema


def test_region_key_quantizes_the_cone() -> None:
    assert (
        region_key(ra_deg=10.1234567, dec_deg=-20.1, radius_arcsec=30.04, row_limit=50)
        == "10.123457:-20.100000:30.0:50"
    )


def test_table_payload_roundtrip() -> None:
    table = CatalogTable(
        catalogue_id="I/350",
        column_names=("_RAJ2000",),
        rows=(
            CatalogRow(
                index=1, ra_deg=10.0, dec_deg=20.0, separation_arcsec=1.5, values=(("ID", "A"),)
            ),
        ),
    )

    restored = table_from_payload("I/350", table_payload(table))

    assert restored == table


class _Store:
    def __init__(self, stored: list[CatalogTable] | None) -> None:
        self._stored = stored
        self.replaced: list[CatalogTable] | None = None

    async def find_fresh(
        self,
        *,
        source: str,
        region_key: str,
        row_limit: int,
    ) -> list[CatalogTable] | None:
        return self._stored

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
        self.replaced = tables


class _Provider:
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
        return [CatalogTable(catalogue_id="I/350")]


class _Readme:
    def fetch(self, catalogue_id: str) -> None:
        return None


async def test_query_region_uses_a_fresh_download() -> None:
    stored = [CatalogTable(catalogue_id="I/350")]
    provider = _Provider()
    lookup = CatalogLookup(
        provider=provider,  # type: ignore[arg-type]
        readme_fetcher=_Readme(),
        query_timeout_s=1,
        downloads=_Store(stored),
    )

    tables, error = await lookup.query_region(
        SkyCoord(10, 20, unit="deg"),
        CatalogRecommendationConfigSchema(),
    )

    assert error is None
    assert tables == stored
    assert provider.calls == 0


async def test_query_region_stores_a_miss() -> None:
    provider = _Provider()
    store = _Store(None)
    lookup = CatalogLookup(
        provider=provider,  # type: ignore[arg-type]
        readme_fetcher=_Readme(),
        query_timeout_s=1,
        downloads=store,
    )

    tables, error = await lookup.query_region(
        SkyCoord(10, 20, unit="deg"),
        CatalogRecommendationConfigSchema(),
    )

    assert error is None
    assert tables == [CatalogTable(catalogue_id="I/350")]
    assert provider.calls == 1
    assert store.replaced == tables
