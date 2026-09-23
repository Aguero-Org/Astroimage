from __future__ import annotations

import asyncio
import time
from io import BytesIO
from typing import Any, cast
from uuid import uuid4

import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.service import FitsService
from astroimage.main import app
from astroimage.sources.deps import gaia_provider_dependency
from astroimage.sources.gaia import GaiaObject
from astroimage.sources.schema import GaiaMatchConfigSchema
from tests.unit.sources.helpers import (
    synthetic_extended_source_image,
    synthetic_point_source_image,
)


def _sources_fits_bytes() -> bytes:
    image, _ = synthetic_point_source_image()
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()


def _wcs_sources_fits_bytes() -> bytes:
    image, _ = synthetic_point_source_image()
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [128, 128]
    wcs.wcs.crval = [10.0, 20.0]
    wcs.wcs.cdelt = [0.001, -0.001]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    buffer = BytesIO()
    fits.PrimaryHDU(image, header=wcs.to_header()).writeto(buffer)
    return buffer.getvalue()


class _RecordingProvider:
    def __init__(self, gaia_objects: list[GaiaObject]) -> None:
        self._gaia_objects = gaia_objects
        self.searches: list[tuple[float, float, float]] = []

    def search_cone(self, center: SkyCoord, radius_arcsec: float) -> list[GaiaObject]:
        self.searches.append((float(center.ra.deg), float(center.dec.deg), radius_arcsec))
        return self._gaia_objects


async def _store_sources(
    fits_service: FitsService,
    db_session: AsyncSession,
) -> str:
    record = await fits_service.store_bytes(_sources_fits_bytes(), source_name="survey.fits")
    await db_session.commit()
    return str(record.id)


async def _poll_gaia_job(
    client: AsyncClient,
    record_id: str,
    job_id: str,
    *,
    headers: dict[str, str] | None = None,
    timeout_s: float = 5.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        response = await client.get(
            f"/image/{record_id}/sources/gaia/jobs/{job_id}",
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        if body.get("status") != "pending":
            return cast(dict[str, Any], body)
        await asyncio.sleep(0.01)
    raise AssertionError("gaia job did not complete in time")


async def _verify_gaia(
    client: AsyncClient,
    record_id: str,
    *,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    response = await client.get(
        f"/image/{record_id}/sources/gaia",
        params=params,
        headers=headers,
    )
    assert response.status_code == 200
    body = cast(dict[str, Any], response.json())
    if body.get("status") != "pending":
        return body
    return await _poll_gaia_job(client, record_id, str(body["job_id"]), headers=headers)


@pytest.mark.asyncio
async def test_detect_sources_returns_point_sources(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_sources(fits_service, db_session)

    response = await client.get(
        f"/image/{record_id}/sources",
        params={"fwhm": "5.0", "sigma": "6.0", "min_snr": "4.0"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source_name"] == "survey.fits"
    assert body["summary"]["extended_count"] == len(body["extended_sources"])
    assert body["summary"]["point_count"] == len(body["point_sources"])
    assert body["summary"]["point_count"] >= 3
    for source in body["point_sources"]:
        assert source["object_type"] == "point"
        assert source["xcentroid"] > 0
        assert source["ycentroid"] > 0
        assert source["snr"] >= 4.0
    for source in body["extended_sources"]:
        assert source["object_type"] == "extended"
    ranks = [source["rank"] for source in body["point_sources"]]
    assert ranks == list(range(1, len(ranks) + 1))
    assert body["gaia_url"].startswith(f"/image/{record_id}/sources/gaia?")
    assert "fwhm=5.0" in body["gaia_url"]
    assert "sigma=6.0" in body["gaia_url"]
    assert f"match_radius_arcsec={GaiaMatchConfigSchema().match_radius_arcsec}" in body["gaia_url"]


@pytest.mark.asyncio
async def test_detect_sources_with_max_sources_limit(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_sources(fits_service, db_session)

    response = await client.get(
        f"/image/{record_id}/sources",
        params={"fwhm": "5.0", "sigma": "6.0", "max_sources": "2"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["point_count"] <= 2


@pytest.mark.asyncio
async def test_detect_sources_returns_extended_sources_on_nebula(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    image, _ = synthetic_extended_source_image()
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="nebula.fits")
    await db_session.commit()

    response = await client.get(f"/image/{record.id}/sources")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["extended_count"] >= 1
    assert body["summary"]["extended_count"] == len(body["extended_sources"])
    for source in body["extended_sources"]:
        assert source["object_type"] == "extended"
        assert source["xcentroid"] > 0
        assert source["ycentroid"] > 0
        assert source["area_pixels"] > 0


@pytest.mark.asyncio
async def test_detect_sources_extended_params_filter_out_regions(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    image, _ = synthetic_extended_source_image()
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="nebula.fits")
    await db_session.commit()

    response = await client.get(
        f"/image/{record.id}/sources",
        params={"ext_min_area": "100000000"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["extended_count"] == 0
    assert body["extended_sources"] == []


@pytest.mark.asyncio
async def test_detect_sources_missing_record_returns_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/image/{uuid4()}/sources")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_detect_sources_noise_only_returns_no_sources(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    rng = np.random.default_rng(3)
    image = rng.normal(scale=5.0, size=(128, 128))
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="noise.fits")
    await db_session.commit()

    response = await client.get(f"/image/{record.id}/sources")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["point_count"] == 0


@pytest.mark.asyncio
async def test_detect_sources_constant_image_raises_bad_request(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    buffer = BytesIO()
    fits.PrimaryHDU(np.zeros((128, 128))).writeto(buffer)
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="flat.fits")
    await db_session.commit()

    response = await client.get(f"/image/{record.id}/sources")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_verify_sources_gaia_matches_stored_wcs_sources(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    buffer = BytesIO()
    buffer.write(_wcs_sources_fits_bytes())
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="wcs.fits")
    await db_session.commit()
    provider = _RecordingProvider(
        [
            GaiaObject(source_id="gaia-a", ra_deg=9.9325, dec_deg=20.0575, gmag=12.0),
            GaiaObject(source_id="gaia-b", ra_deg=10.0225, dec_deg=20.0875, gmag=12.5),
            GaiaObject(source_id="gaia-c", ra_deg=10.0625, dec_deg=19.9475, gmag=13.0),
        ]
    )
    app.dependency_overrides[gaia_provider_dependency] = lambda: provider
    try:
        body = await _verify_gaia(
            client,
            str(record.id),
            params={"fwhm": "5.0", "sigma": "6.0", "match_radius_arcsec": "60"},
            headers={"X-Client-Id": "alice"},
        )
    finally:
        app.dependency_overrides.pop(gaia_provider_dependency, None)

    assert body["wcs_present"] is True
    assert body["queried"] is True
    assert body["error"] is None
    assert body["match_radius_arcsec"] == 60.0
    assert body["summary"]["point"]["matched"] >= 1
    assert any(row["gaia_match"] for row in body["matches"])
    assert len(provider.searches) == 3
    expected_centers = {
        (9.9325, 20.0575),
        (10.0225, 20.0875),
        (10.0625, 19.9475),
    }
    got_centers = {(center_ra, center_dec) for center_ra, center_dec, _ in provider.searches}
    assert all(
        any(
            center_ra == pytest.approx(expected_ra, abs=0.02)
            and center_dec == pytest.approx(expected_dec, abs=0.02)
            for expected_ra, expected_dec in expected_centers
        )
        for center_ra, center_dec in got_centers
    )
    assert all(radius >= 60.0 for _, _, radius in provider.searches)


@pytest.mark.asyncio
async def test_verify_sources_gaia_endpoint_conserves_detection_params(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    buffer = BytesIO()
    buffer.write(_wcs_sources_fits_bytes())
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="wcs.fits")
    await db_session.commit()
    provider = _RecordingProvider([])
    app.dependency_overrides[gaia_provider_dependency] = lambda: provider
    try:
        body = await _verify_gaia(
            client,
            str(record.id),
            params={"fwhm": "5.0", "sigma": "6.0", "min_snr": "4.0"},
        )
    finally:
        app.dependency_overrides.pop(gaia_provider_dependency, None)

    assert body["summary"]["point"]["count"] >= 3
    assert body["summary"]["point"]["matched"] == 0
    assert (
        len(provider.searches) == 4
    )  # 3 bloques + fallback single-query (paridad TPI gaia.py:183-204)
    assert not any(row["gaia_match"] for row in body["matches"])


@pytest.mark.asyncio
async def test_verify_sources_gaia_without_wcs_skips_query(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_sources(fits_service, db_session)
    provider = _RecordingProvider([])
    app.dependency_overrides[gaia_provider_dependency] = lambda: provider
    try:
        body = await _verify_gaia(
            client,
            record_id,
            headers={"X-Client-Id": "alice"},
        )
    finally:
        app.dependency_overrides.pop(gaia_provider_dependency, None)

    assert body["wcs_present"] is False
    assert body["queried"] is False
    assert body["error"] is None
    assert provider.searches == []


@pytest.mark.asyncio
async def test_verify_sources_gaia_isolates_queries_by_client_id(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    buffer = BytesIO()
    buffer.write(_wcs_sources_fits_bytes())
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="wcs.fits")
    await db_session.commit()
    provider = _RecordingProvider(
        [GaiaObject(source_id="gaia-a", ra_deg=9.9325, dec_deg=20.0575, gmag=12.0)]
    )
    app.dependency_overrides[gaia_provider_dependency] = lambda: provider
    try:
        expected_blocks = 0
        for client_id in ("alice", "bob"):
            body = await _verify_gaia(
                client,
                str(record.id),
                params={"fwhm": "5.0", "sigma": "6.0"},
                headers={"X-Client-Id": client_id},
            )
            assert body["summary"]["point"]["count"] >= 3
            expected_blocks += min(
                8,
                body["summary"]["point"]["count"],
            )
    finally:
        app.dependency_overrides.pop(gaia_provider_dependency, None)

    assert len(provider.searches) == expected_blocks


@pytest.mark.asyncio
async def test_verify_sources_gaia_serves_cached_result_on_resubmit(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    buffer = BytesIO()
    buffer.write(_wcs_sources_fits_bytes())
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="wcs.fits")
    await db_session.commit()
    provider = _RecordingProvider([])
    app.dependency_overrides[gaia_provider_dependency] = lambda: provider
    try:
        first = await _verify_gaia(
            client,
            str(record.id),
            headers={"X-Client-Id": "alice"},
        )
        second = await _verify_gaia(
            client,
            str(record.id),
            headers={"X-Client-Id": "alice"},
        )
    finally:
        app.dependency_overrides.pop(gaia_provider_dependency, None)

    assert second["queried"] is True
    assert second == first
    assert (
        len(provider.searches) == 4
    )  # 3 bloques + fallback single-query (paridad TPI gaia.py:183-204)


@pytest.mark.asyncio
async def test_verify_sources_gaia_blocks_and_returns_completed_result(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_sources(fits_service, db_session)
    provider = _RecordingProvider([])
    app.dependency_overrides[gaia_provider_dependency] = lambda: provider
    try:
        response = await client.get(
            f"/image/{record_id}/sources/gaia",
            headers={"X-Client-Id": "alice"},
        )
    finally:
        app.dependency_overrides.pop(gaia_provider_dependency, None)

    assert response.status_code == 200
    body = cast(dict[str, Any], response.json())
    assert body["queried"] is False
    assert body["error"] is None


@pytest.mark.asyncio
async def test_verify_sources_gaia_constant_image_fails_job_with_bad_request(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    buffer = BytesIO()
    fits.PrimaryHDU(np.zeros((64, 64))).writeto(buffer)
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="flat.fits")
    await db_session.commit()
    provider = _RecordingProvider([])
    app.dependency_overrides[gaia_provider_dependency] = lambda: provider
    try:
        response = await client.get(
            f"/image/{record.id}/sources/gaia",
            headers={"X-Client-Id": "alice"},
        )
    finally:
        app.dependency_overrides.pop(gaia_provider_dependency, None)

    assert response.status_code == 400
    assert response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_sources_gaia_missing_record_returns_not_found(
    client: AsyncClient,
) -> None:
    response = await client.get(f"/image/{uuid4()}/sources/gaia")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_poll_gaia_job_unknown_job_returns_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/image/{uuid4()}/sources/gaia/jobs/unknown-job")

    assert response.status_code == 404
