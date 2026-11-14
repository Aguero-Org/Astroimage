from __future__ import annotations

from astropy.coordinates import SkyCoord

from astroimage.catalogs.download import CatalogDownloadHit, table_from_payload, table_payload
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
    def __init__(self, stored: CatalogDownloadHit | None) -> None:
        self._stored = stored
        self.replaced: list[CatalogTable] | None = None

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
        del region_suffix
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


class _RaisingProvider(_Provider):
    def __init__(self, error: Exception) -> None:
        super().__init__()
        self._error = error

    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
    ) -> list[CatalogTable]:
        self.calls += 1
        raise self._error


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
        downloads=_Store(CatalogDownloadHit(tables=stored, covered=False)),
    )

    tables, error = await lookup.query_region(
        SkyCoord(10, 20, unit="deg"),
        CatalogRecommendationConfigSchema(),
    )

    assert error is None
    assert tables == stored
    assert provider.calls == 0


async def test_query_region_narrows_a_covered_download() -> None:
    stored = [
        CatalogTable(
            catalogue_id="I/350",
            rows=(
                CatalogRow(index=0, ra_deg=10.0, dec_deg=20.0, separation_arcsec=20.0),
                CatalogRow(index=1, ra_deg=10.0, dec_deg=21.0, separation_arcsec=3600.0),
            ),
        ),
        CatalogTable(
            catalogue_id="II/1",
            rows=(CatalogRow(index=0, ra_deg=10.0, dec_deg=21.0, separation_arcsec=3600.0),),
        ),
    ]
    provider = _Provider()
    lookup = CatalogLookup(
        provider=provider,  # type: ignore[arg-type]
        readme_fetcher=_Readme(),
        query_timeout_s=1,
        downloads=_Store(CatalogDownloadHit(tables=stored, covered=True)),
    )

    tables, error = await lookup.query_region(
        SkyCoord(10, 20, unit="deg"),
        CatalogRecommendationConfigSchema(search_radius_arcsec=30.0),
    )

    assert error is None
    assert [table.catalogue_id for table in tables] == ["I/350"]
    assert [row.index for row in tables[0].rows] == [0]
    separation = tables[0].rows[0].separation_arcsec
    assert separation is not None
    assert separation < 1e-6
    assert provider.calls == 0


async def test_query_region_drops_rows_without_coordinates_when_narrowing() -> None:
    stored = [
        CatalogTable(
            catalogue_id="I/350",
            rows=(
                CatalogRow(index=0, ra_deg=10.0, dec_deg=20.0),
                CatalogRow(index=1, ra_deg=None, dec_deg=None),
            ),
        ),
        CatalogTable(
            catalogue_id="II/1",
            rows=(CatalogRow(index=0, ra_deg=None, dec_deg=None),),
        ),
    ]
    lookup = CatalogLookup(
        provider=_Provider(),  # type: ignore[arg-type]
        readme_fetcher=_Readme(),
        query_timeout_s=1,
        downloads=_Store(CatalogDownloadHit(tables=stored, covered=True)),
    )

    tables, error = await lookup.query_region(
        SkyCoord(10, 20, unit="deg"),
        CatalogRecommendationConfigSchema(search_radius_arcsec=30.0),
    )

    assert error is None
    assert [table.catalogue_id for table in tables] == ["I/350"]
    assert [row.index for row in tables[0].rows] == [0]


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


async def test_query_region_reports_vizier_unavailable() -> None:
    lookup = CatalogLookup(
        provider=_RaisingProvider(ConnectionError("boom")),  # type: ignore[arg-type]
        readme_fetcher=_Readme(),
        query_timeout_s=1,
        downloads=_Store(None),
    )

    tables, error = await lookup.query_region(
        SkyCoord(10, 20, unit="deg"),
        CatalogRecommendationConfigSchema(),
    )

    assert tables == []
    assert error == (
        "La consulta a VizieR falló en todos sus servidores. Probá de nuevo en unos minutos."
    )


async def test_query_region_reports_vizier_timeout() -> None:
    lookup = CatalogLookup(
        provider=_RaisingProvider(TimeoutError()),  # type: ignore[arg-type]
        readme_fetcher=_Readme(),
        query_timeout_s=1,
        downloads=_Store(None),
    )

    tables, error = await lookup.query_region(
        SkyCoord(10, 20, unit="deg"),
        CatalogRecommendationConfigSchema(),
    )

    assert tables == []
    assert error == (
        "La consulta a VizieR superó el límite de 1 s. Probá de nuevo en unos minutos."
    )
