from __future__ import annotations

import asyncio
import time
from io import BytesIO
from typing import Any, cast
from uuid import uuid4

import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.catalogs.deps import readme_fetcher_dependency, vizier_provider_dependency
from astroimage.catalogs.model import CatalogMetadata, CatalogRow, CatalogTable
from astroimage.catalogs.readme import ReadmeData
from astroimage.fits.service import FitsService
from astroimage.main import app
from tests.unit.sources.helpers import synthetic_point_source_image

_GAIA_ID = "3403818138212571264"
_BIBCODE = "2016A&A...595A...1G"
_DOI = "10.1051/0004-6361/201629272"


def _wcs_point_source_fits_bytes() -> bytes:
    image, _ = synthetic_point_source_image()
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [128, 128]
    wcs.wcs.crval = [10.0, 20.0]
    wcs.wcs.cdelt = [0.001, -0.001]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    buffer = BytesIO()
    fits.PrimaryHDU(image, header=wcs.to_header()).writeto(buffer)
    return buffer.getvalue()


def _plain_fits_bytes() -> bytes:
    image, _ = synthetic_point_source_image()
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()


class _RecordingProvider:
    def __init__(self, tables: list[CatalogTable]) -> None:
        self._tables = tables
        self.calls: list[tuple[float, float, float, int]] = []

    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
    ) -> list[CatalogTable]:
        self.calls.append((float(center.ra.deg), float(center.dec.deg), radius_arcsec, row_limit))
        return list(self._tables)

    def catalog_metadata(self, catalogue_id: str) -> CatalogMetadata:
        return CatalogMetadata(
            catalogue_id=catalogue_id,
            title="Gaia DR3 part 1",
            authors="Gaia Collaboration",
            doi=_DOI,
            webpage="https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/A+A/595/A1",
            origin_article=_BIBCODE,
        )


class _RecordingReadmeFetcher:
    def fetch(self, catalogue_id: str) -> ReadmeData | None:
        return ReadmeData(
            url="https://cdsarc.cds.unistra.fr/ftp/cats/J/A+A/595/A1/ReadMe",
            reference_bibcodes=(_BIBCODE,),
            reference_dois=(_DOI,),
        )


async def _store_wcs_record(fits_service: FitsService, db_session: AsyncSession) -> str:
    record = await fits_service.store_bytes(
        _wcs_point_source_fits_bytes(),
        source_name="survey.fits",
    )
    await db_session.commit()
    return str(record.id)


async def _poll_job(
    client: AsyncClient,
    record_id: str,
    job_id: str,
    *,
    headers: dict[str, str] | None = None,
    timeout_s: float = 10.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        response = await client.get(
            f"/image/{record_id}/catalogs/recommendations/jobs/{job_id}",
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        if body.get("status") != "pending":
            return cast(dict[str, Any], body)
        await asyncio.sleep(0.01)
    raise AssertionError("catalog job did not complete in time")


async def _recommend(
    client: AsyncClient,
    record_id: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    response = await client.get(
        f"/image/{record_id}/catalogs/recommendations",
        params=params,
        headers=headers,
    )
    assert response.status_code == 200
    body = cast(dict[str, Any], response.json())
    if body.get("status") != "pending":
        return body
    return await _poll_job(client, record_id, str(body["job_id"]), headers=headers)


_TOP_TABLE = CatalogTable(
    catalogue_id="J/A+A/595/A1",
    rows=(
        CatalogRow(
            index=0,
            ra_deg=9.9325,
            dec_deg=20.0575,
            separation_arcsec=0.2,
            values=(("Source", _GAIA_ID), ("_2MASS", "2MASS J05342669+2200301")),
        ),
    ),
)


@pytest.mark.asyncio
async def test_recommend_catalogs_ranks_and_scores(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_wcs_record(fits_service, db_session)
    provider = _RecordingProvider(
        [
            CatalogTable(
                catalogue_id="I/350",
                rows=(CatalogRow(index=0, separation_arcsec=3.0, values=()),),
            ),
            _TOP_TABLE,
        ]
    )
    app.dependency_overrides[vizier_provider_dependency] = lambda: provider
    app.dependency_overrides[readme_fetcher_dependency] = _RecordingReadmeFetcher
    try:
        body = await _recommend(
            client,
            record_id,
            params={"identifiers": [_GAIA_ID, "2MASS J05342669+2200301"]},
            headers={"X-Client-Id": "alice"},
        )
    finally:
        app.dependency_overrides.pop(vizier_provider_dependency, None)
        app.dependency_overrides.pop(readme_fetcher_dependency, None)

    assert body["wcs_present"] is True
    assert body["queried"] is True
    assert body["error"] is None
    assert body["ra_deg"] == pytest.approx(10.0)
    assert body["summary"]["catalogue_count"] == 2
    assert body["summary"]["object_in_table_count"] == 1

    top, second = body["recommendations"]
    assert top["rank"] == 1
    assert top["catalogue_id"] == "J/A+A/595/A1"
    assert top["match_type"] == "OBJECT_IN_TABLE"
    assert top["identifier_score"] == 50.0
    assert top["total_score"] == 130.0
    assert top["paper_ads_url"] is not None
    assert second["catalogue_id"] == "I/350"
    assert second["match_type"] == "CATALOGUE_ONLY"
    assert provider.calls[0][2] == 10.0


@pytest.mark.asyncio
async def test_recommend_catalogs_caches_result_per_client(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_wcs_record(fits_service, db_session)
    provider = _RecordingProvider([_TOP_TABLE])
    app.dependency_overrides[vizier_provider_dependency] = lambda: provider
    app.dependency_overrides[readme_fetcher_dependency] = _RecordingReadmeFetcher
    try:
        first = await _recommend(client, record_id, headers={"X-Client-Id": "alice"})
        second = await _recommend(client, record_id, headers={"X-Client-Id": "alice"})
    finally:
        app.dependency_overrides.pop(vizier_provider_dependency, None)
        app.dependency_overrides.pop(readme_fetcher_dependency, None)

    assert first == second
    assert len(provider.calls) == 1


@pytest.mark.asyncio
async def test_recommend_catalogs_without_wcs_skips_query(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record = await fits_service.store_bytes(_plain_fits_bytes(), source_name="plain.fits")
    await db_session.commit()
    provider = _RecordingProvider([_TOP_TABLE])
    app.dependency_overrides[vizier_provider_dependency] = lambda: provider
    app.dependency_overrides[readme_fetcher_dependency] = _RecordingReadmeFetcher
    try:
        body = await _recommend(client, str(record.id), headers={"X-Client-Id": "alice"})
    finally:
        app.dependency_overrides.pop(vizier_provider_dependency, None)
        app.dependency_overrides.pop(readme_fetcher_dependency, None)

    assert body["wcs_present"] is False
    assert body["queried"] is False
    assert body["error"] is None
    assert provider.calls == []


@pytest.mark.asyncio
async def test_recommend_catalogs_with_crossmatch_attaches_matches(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_wcs_record(fits_service, db_session)
    provider = _RecordingProvider([_TOP_TABLE])
    app.dependency_overrides[vizier_provider_dependency] = lambda: provider
    app.dependency_overrides[readme_fetcher_dependency] = _RecordingReadmeFetcher
    try:
        body = await _recommend(
            client,
            record_id,
            params={
                "crossmatch": "true",
                "crossmatch_top": "1",
                "crossmatch_radius_arcsec": "20",
            },
            headers={"X-Client-Id": "alice"},
        )
    finally:
        app.dependency_overrides.pop(vizier_provider_dependency, None)
        app.dependency_overrides.pop(readme_fetcher_dependency, None)

    assert body["queried"] is True
    crossmatch = body["recommendations"][0]["crossmatch"]
    assert crossmatch is not None
    assert crossmatch["matched_count"] >= 1
    assert any(row["matched"] for row in crossmatch["matches"])


@pytest.mark.asyncio
async def test_recommend_catalogs_missing_record_returns_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/image/{uuid4()}/catalogs/recommendations")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_poll_unknown_catalog_job_returns_not_found(client: AsyncClient) -> None:
    response = await client.get(
        f"/image/{uuid4()}/catalogs/recommendations/jobs/unknown-job",
    )

    assert response.status_code == 404
