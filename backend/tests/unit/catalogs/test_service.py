from __future__ import annotations

from collections.abc import Sequence
from io import BytesIO
from typing import cast

import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS

from astroimage.catalogs.cache import CatalogRecommendationCache
from astroimage.catalogs.model import CatalogMetadata, CatalogRow, CatalogTable
from astroimage.catalogs.papers import PaperIdentifier, PaperRecord
from astroimage.catalogs.readme import ReadmeData
from astroimage.catalogs.schema import CatalogRecommendationConfigSchema
from astroimage.catalogs.service import CatalogRecommendationService
from astroimage.catalogs.vizier import VizierCatalogProvider
from astroimage.fits.service import FitsService

_GAIA_ID = "3403818138212571264"
_BIBCODE = "2016A&A...595A...1G"
_DOI = "10.1051/0004-6361/201629272"


def _wcs_payload() -> bytes:
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [2.0, 2.0]
    wcs.wcs.crval = [10.0, 20.0]
    wcs.wcs.cdelt = [0.001, -0.001]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    buffer = BytesIO()
    fits.PrimaryHDU(np.ones((4, 4)), header=wcs.to_header()).writeto(buffer)
    return buffer.getvalue()


def _plain_payload() -> bytes:
    buffer = BytesIO()
    fits.PrimaryHDU(np.ones((4, 4))).writeto(buffer)
    return buffer.getvalue()


def _row(index: int, separation: float, values: tuple[tuple[str, str], ...]) -> CatalogRow:
    return CatalogRow(index=index, separation_arcsec=separation, values=values)


class _FakeProvider:
    def __init__(
        self,
        tables: list[CatalogTable],
        metadata: dict[str, CatalogMetadata] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._tables = tables
        self._metadata = metadata or {}
        self._error = error
        self.calls: list[tuple[float, float, float, int]] = []

    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
    ) -> list[CatalogTable]:
        self.calls.append((float(center.ra.deg), float(center.dec.deg), radius_arcsec, row_limit))
        if self._error is not None:
            raise self._error
        return list(self._tables)

    def catalog_metadata(self, catalogue_id: str) -> CatalogMetadata:
        return self._metadata.get(catalogue_id, CatalogMetadata(catalogue_id=catalogue_id))


class _FakeReadmeFetcher:
    def __init__(self, data: dict[str, ReadmeData] | None = None) -> None:
        self._data = data or {}

    def fetch(self, catalogue_id: str) -> ReadmeData | None:
        return self._data.get(catalogue_id)


def _service(provider: _FakeProvider, readme: _FakeReadmeFetcher) -> CatalogRecommendationService:
    return CatalogRecommendationService(
        fits=cast(FitsService, None),
        provider=cast(VizierCatalogProvider, provider),
        readme_fetcher=readme,
        cache=CatalogRecommendationCache(),
    )


@pytest.mark.asyncio
async def test_recommend_ranks_scored_catalogues() -> None:
    provider = _FakeProvider(
        tables=[
            CatalogTable(
                catalogue_id="I/350",
                rows=(_row(0, 3.0, (("_2MASS", "2MASS J00000000+0000000"),)),),
            ),
            CatalogTable(
                catalogue_id="J/A+A/595/A1",
                rows=(
                    _row(
                        0,
                        0.2,
                        (("Source", _GAIA_ID), ("_2MASS", "2MASS J05342669+2200301")),
                    ),
                ),
            ),
        ],
        metadata={
            "J/A+A/595/A1": CatalogMetadata(
                catalogue_id="J/A+A/595/A1",
                title="Gaia DR3 part 1",
                authors="Gaia Collaboration",
                doi=_DOI,
                webpage="https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/A+A/595/A1",
                origin_article=_BIBCODE,
            ),
        },
    )
    readme = _FakeReadmeFetcher(
        {
            "J/A+A/595/A1": ReadmeData(
                url="https://cdsarc.cds.unistra.fr/ftp/cats/J/A+A/595/A1/ReadMe",
                reference_bibcodes=(_BIBCODE,),
                reference_dois=(_DOI,),
            ),
        }
    )
    config = CatalogRecommendationConfigSchema(identifiers=[_GAIA_ID, "2MASS J05342669+2200301"])
    result = await _service(provider, readme).recommend(_wcs_payload(), config=config)

    assert result.queried is True
    assert result.wcs_present is True
    assert result.ra_deg == pytest.approx(10.0)
    assert result.summary.catalogue_count == 2
    assert provider.calls[0][2] == config.search_radius_arcsec

    top, second = result.recommendations
    assert top.catalogue_id == "J/A+A/595/A1"
    assert top.match_type == "OBJECT_IN_TABLE"
    assert top.identifier_match is True
    assert top.spatial_match is True
    assert top.identifier_score == 50.0
    assert top.spatial_score == 40.0
    assert top.paper_score == 25.0
    assert top.doi_score == 15.0
    assert top.total_score == 130.0
    assert top.paper_bibcode == _BIBCODE
    assert top.paper_ads_url is not None
    assert top.readme_url is not None

    assert second.catalogue_id == "I/350"
    assert second.match_type == "CATALOGUE_ONLY"
    assert second.spatial_score == 10.0
    assert second.total_score == 10.0


@pytest.mark.asyncio
async def test_recommend_without_wcs_skips_the_query() -> None:
    provider = _FakeProvider(tables=[])
    result = await _service(provider, _FakeReadmeFetcher()).recommend(_plain_payload())

    assert result.wcs_present is False
    assert result.queried is False
    assert result.error is None
    assert provider.calls == []


@pytest.mark.asyncio
async def test_recommend_surfaces_query_errors() -> None:
    provider = _FakeProvider(tables=[], error=RuntimeError("tap down"))
    result = await _service(provider, _FakeReadmeFetcher()).recommend(_wcs_payload())

    assert result.wcs_present is True
    assert result.queried is False
    assert result.error is not None
    assert "tap down" in result.error


class _FakePaperLookup:
    def __init__(self, records: list[PaperRecord]) -> None:
        self.records = records
        self.calls: list[list[str]] = []

    def fetch(self, identifiers: Sequence[PaperIdentifier]) -> list[PaperRecord]:
        self.calls.append([identifier.lookup_key or "" for identifier in identifiers])
        return self.records


class _FakePaperStore:
    def __init__(self, fresh: dict[str, PaperRecord] | None = None) -> None:
        self.fresh = fresh or {}
        self.saved: list[PaperRecord] = []

    async def find_fresh(self, keys: Sequence[str]) -> dict[str, PaperRecord]:
        return {key: self.fresh[key] for key in keys if key in self.fresh}

    async def save(self, records: Sequence[PaperRecord]) -> None:
        self.saved.extend(records)


@pytest.mark.asyncio
async def test_recommend_attaches_paper_title_from_lookup() -> None:
    provider = _FakeProvider(
        tables=[CatalogTable(catalogue_id="J/A+A/595/A1")],
        metadata={
            "J/A+A/595/A1": CatalogMetadata(
                catalogue_id="J/A+A/595/A1",
                origin_article=_BIBCODE,
                doi=_DOI,
            )
        },
    )
    lookup = _FakePaperLookup(
        [
            PaperRecord(
                lookup_key=_BIBCODE,
                bibcode=_BIBCODE,
                doi=_DOI,
                title="Gaia Data Release 1",
                abstract="Positions and photometry.",
            )
        ]
    )
    store = _FakePaperStore()
    service = CatalogRecommendationService(
        fits=cast(FitsService, None),
        provider=cast(VizierCatalogProvider, provider),
        readme_fetcher=_FakeReadmeFetcher(),
        cache=CatalogRecommendationCache(),
        paper_lookup=lookup,
        paper_store=store,
    )

    result = await service.recommend(_wcs_payload())

    assert result.papers[0].title == "Gaia Data Release 1"
    assert result.papers[0].abstract == "Positions and photometry."
    assert lookup.calls == [[_BIBCODE]]
    assert store.saved[0].lookup_key == _BIBCODE


@pytest.mark.asyncio
async def test_recommend_uses_a_cached_paper_without_lookup() -> None:
    provider = _FakeProvider(
        tables=[CatalogTable(catalogue_id="J/A+A/595/A1")],
        metadata={
            "J/A+A/595/A1": CatalogMetadata(
                catalogue_id="J/A+A/595/A1",
                origin_article=_BIBCODE,
            )
        },
    )
    lookup = _FakePaperLookup([])
    store = _FakePaperStore(
        {
            _BIBCODE: PaperRecord(
                lookup_key=_BIBCODE,
                bibcode=_BIBCODE,
                title="Cached title",
                abstract="Cached abstract",
            )
        }
    )
    service = CatalogRecommendationService(
        fits=cast(FitsService, None),
        provider=cast(VizierCatalogProvider, provider),
        readme_fetcher=_FakeReadmeFetcher(),
        cache=CatalogRecommendationCache(),
        paper_lookup=lookup,
        paper_store=store,
    )

    result = await service.recommend(_wcs_payload())

    assert result.papers[0].title == "Cached title"
    assert lookup.calls == []
    assert store.saved == []
