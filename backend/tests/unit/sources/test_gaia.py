from __future__ import annotations

import asyncio
import io
import threading
import time
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS

from astroimage.fits.model import FitsRecord
from astroimage.fits.service import FitsService
from astroimage.sources.gaia import (
    GaiaObject,
    match_sources_to_gaia,
    search_radius_arcsec,
)
from astroimage.sources.schema import (
    GaiaMatchConfigSchema,
    PointDetectionConfigSchema,
)
from astroimage.sources.service import (
    GaiaVerificationService,
    SourceDetectionService,
    _merge_gaia_objects,
)
from tests.unit.sources.helpers import (
    fits_bytes_from_image,
    synthetic_point_source_image,
)


def _wcs_fits_bytes() -> bytes:
    image, _ = synthetic_point_source_image()
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [128, 128]
    wcs.wcs.crval = [10.0, 20.0]
    wcs.wcs.cdelt = [0.001, -0.001]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    buffer = io.BytesIO()
    fits.PrimaryHDU(image, header=wcs.to_header()).writeto(buffer)
    return buffer.getvalue()


class _FakeGaiaProvider:
    def __init__(self, gaia_objects: list[GaiaObject]) -> None:
        self._gaia_objects = gaia_objects
        self.searches: list[tuple[float, float, float]] = []

    def search_cone(self, center: SkyCoord, radius_arcsec: float) -> list[GaiaObject]:
        self.searches.append((float(center.ra.deg), float(center.dec.deg), radius_arcsec))
        return self._gaia_objects


class _FailingGaiaProvider:
    def search_cone(self, center: SkyCoord, radius_arcsec: float) -> list[GaiaObject]:
        raise RuntimeError("provider boom")


class _SlowGaiaProvider:
    def search_cone(self, center: SkyCoord, radius_arcsec: float) -> list[GaiaObject]:
        time.sleep(0.8)
        return []


class _TrackingProvider:
    def __init__(self, delay_s: float = 2.0) -> None:
        self._delay_s = delay_s
        self._lock = threading.Lock()
        self._in_flight = 0
        self.searches: list[tuple[float, float, float]] = []
        self.max_concurrent = 0

    def search_cone(self, center: SkyCoord, radius_arcsec: float) -> list[GaiaObject]:
        with self._lock:
            self._in_flight += 1
            self.max_concurrent = max(self.max_concurrent, self._in_flight)
        self.searches.append((float(center.ra.deg), float(center.dec.deg), radius_arcsec))
        try:
            time.sleep(self._delay_s)
            return []
        finally:
            with self._lock:
                self._in_flight -= 1


class _FakeFitsService:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._record = FitsRecord(
            id=uuid4(),
            object_key="fits/record-uuid.fits",
            original_filename="wcs.fits",
            size_bytes=len(payload),
            created_at=datetime.now(UTC),
            metadata_payload={},
        )

    async def get_record(self, record_id: object) -> FitsRecord:
        return self._record

    async def get_payload(self, record: object) -> bytes:
        return self._payload

    async def update_record_metadata(
        self,
        record: object,
        payload: object,
        *,
        hdu_index: object = None,
    ) -> FitsRecord:
        return self._record


def test_verify_with_wcs_matches_sources_to_gaia() -> None:
    payload = _wcs_fits_bytes()
    expected_world = {
        (9.9325, 20.0575),
        (10.0225, 20.0875),
        (10.0625, 19.9475),
    }
    provider = _FakeGaiaProvider(
        [
            GaiaObject(
                source_id="gaia-a",
                ra_deg=9.9325,
                dec_deg=20.0575,
                gmag=13.5,
            ),
            GaiaObject(
                source_id="gaia-b",
                ra_deg=10.0225,
                dec_deg=20.0875,
                gmag=15.2,
            ),
            GaiaObject(
                source_id="gaia-c",
                ra_deg=10.0625,
                dec_deg=19.9475,
                gmag=14.0,
            ),
        ]
    )
    service = GaiaVerificationService(
        detection_service=SourceDetectionService(),
        provider=provider,
    )

    result = service.verify(
        payload,
        source_name="wcs.fits",
        config=PointDetectionConfigSchema(sigma=6.0, fwhm=5.0),
        gaia_config=GaiaMatchConfigSchema(match_radius_arcsec=60.0),
    )

    assert result.wcs_present is True
    assert result.queried is True
    assert result.error is None
    assert result.match_radius_arcsec == 60.0
    point_rows = [row for row in result.matches if row.object_type == "point"]
    assert len(point_rows) >= 3
    assert all(row.gaia_match is True for row in point_rows)
    assert all(row.gaia_separation_arcsec is not None for row in point_rows)
    assert all(row.gaia_gmag is not None for row in point_rows)
    for row in point_rows:
        assert any(
            row.ra_deg == pytest.approx(expected_ra, abs=0.02)
            and row.dec_deg == pytest.approx(expected_dec, abs=0.02)
            for expected_ra, expected_dec in expected_world
        )
    assert result.summary.point.count == len(point_rows)
    assert result.summary.point.matched == len(point_rows)
    assert result.summary.point.match_rate == pytest.approx(1.0)
    assert result.summary.point.median_separation_arcsec is not None
    assert result.summary.extended.count == 0
    assert len(provider.searches) == 1
    assert provider.searches[0][2] >= 60.0


def test_verify_without_wcs_skips_gaia_query() -> None:
    image, _ = synthetic_point_source_image()
    payload = fits_bytes_from_image(image)
    provider = _FakeGaiaProvider([GaiaObject(source_id="gaia-1", ra_deg=10.0, dec_deg=20.0)])
    service = GaiaVerificationService(
        detection_service=SourceDetectionService(),
        provider=provider,
    )

    result = service.verify(payload, source_name="no-wcs.fits")

    assert result.wcs_present is False
    assert result.queried is False
    assert result.error is None
    assert result.matches
    assert all(row.gaia_match is False for row in result.matches)
    assert provider.searches == []
    assert result.summary.point.matched == 0


def test_verify_reports_provider_failure_in_error_field() -> None:
    payload = _wcs_fits_bytes()
    service = GaiaVerificationService(
        detection_service=SourceDetectionService(),
        provider=_FailingGaiaProvider(),
    )

    result = service.verify(
        payload,
        source_name="wcs.fits",
        config=PointDetectionConfigSchema(sigma=6.0, fwhm=5.0),
    )

    assert result.queried is False
    assert result.error is not None
    assert "Gaia query failed" in result.error
    assert all(row.gaia_match is False for row in result.matches)


def test_match_sources_returns_closest_catalog_object() -> None:
    coordinate = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)
    gaia_objects = [
        GaiaObject(source_id="far", ra_deg=10.005, dec_deg=20.0),
        GaiaObject(source_id="near", ra_deg=10.0001, dec_deg=20.0),
    ]

    matches = match_sources_to_gaia(
        [coordinate],
        gaia_objects,
        match_radius_arcsec=4.0,
        probability_power=2.0,
    )
    match = matches[0]
    assert match.matched is True
    assert match.gaia_source_id == "near"
    assert match.separation_arcsec == pytest.approx(0.36, abs=0.05)
    assert 0.0 < match.probability < 1.0

    misses = match_sources_to_gaia(
        [coordinate],
        gaia_objects,
        match_radius_arcsec=0.01,
        probability_power=2.0,
    )
    assert misses[0].matched is False
    assert misses[0].probability == 0.0


def test_match_sources_with_empty_catalog_returns_unmatched_rows() -> None:
    coordinate = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)

    matches = match_sources_to_gaia(
        [coordinate],
        [],
        match_radius_arcsec=4.0,
        probability_power=2.0,
    )

    assert len(matches) == 1
    assert matches[0].matched is False
    assert matches[0].gaia_source_id is None


def test_search_radius_clamps_to_minimum() -> None:
    center = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)

    radius = search_radius_arcsec(
        center,
        [center],
        match_radius_arcsec=1.0,
    )

    assert radius == 60.0


def test_merge_gaia_objects_deduplicates_overlapping_blocks() -> None:
    first = GaiaObject(source_id="gaia-1", ra_deg=10.0, dec_deg=20.0, gmag=13.0)
    duplicate = GaiaObject(source_id="gaia-1", ra_deg=10.0, dec_deg=20.0, gmag=99.0)
    other = GaiaObject(source_id="gaia-2", ra_deg=11.0, dec_deg=21.0)

    merged = _merge_gaia_objects([[first, duplicate], [other, first]])

    assert [obj.source_id for obj in merged] == ["gaia-1", "gaia-2"]
    assert merged[0].gmag == 13.0


@pytest.mark.asyncio
async def test_verify_from_record_returns_matches() -> None:
    payload = _wcs_fits_bytes()
    fits_service = cast(FitsService, _FakeFitsService(payload))
    provider = _FakeGaiaProvider(
        [
            GaiaObject(
                source_id="gaia-a",
                ra_deg=9.9325,
                dec_deg=20.0575,
                gmag=13.5,
            ),
        ]
    )
    service = GaiaVerificationService(
        detection_service=SourceDetectionService(fits=fits_service),
        fits=fits_service,
        provider=provider,
    )

    result = await service.verify_from_record(
        uuid4(),
        config=PointDetectionConfigSchema(sigma=6.0, fwhm=5.0),
        gaia_config=GaiaMatchConfigSchema(match_radius_arcsec=60.0),
    )

    assert result.queried is True
    assert result.error is None
    assert result.wcs_present is True
    assert any(row.gaia_match for row in result.matches)
    assert len(provider.searches) == 3


@pytest.mark.asyncio
async def test_gaia_block_queries_run_concurrently_across_thread_pool() -> None:
    payload = _wcs_fits_bytes()
    fits_service = cast(FitsService, _FakeFitsService(payload))
    provider = _TrackingProvider(delay_s=1.0)
    service = GaiaVerificationService(
        detection_service=SourceDetectionService(fits=fits_service),
        fits=fits_service,
        provider=provider,
        query_timeout_s=30.0,
    )

    started = time.perf_counter()
    result = await service.verify_from_record(
        uuid4(),
        config=PointDetectionConfigSchema(sigma=6.0, fwhm=5.0),
    )
    elapsed = time.perf_counter() - started

    assert result.queried is True
    assert (
        len(provider.searches) == 4
    )  # 3 bloques + fallback single-query (paridad TPI gaia.py:183-204)
    assert provider.max_concurrent == 3
    assert elapsed < 3.0


@pytest.mark.asyncio
async def test_gaia_splits_many_sources_into_eight_blocks() -> None:
    positions = (
        (40, 40),
        (40, 90),
        (40, 140),
        (40, 190),
        (160, 40),
        (160, 90),
        (160, 140),
        (160, 190),
        (140, 215),
        (90, 125),
        (130, 60),
        (100, 45),
    )
    image, _ = synthetic_point_source_image(positions=positions, noise_sigma=2.0)
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [128, 128]
    wcs.wcs.crval = [10.0, 20.0]
    wcs.wcs.cdelt = [0.001, -0.001]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    buffer = io.BytesIO()
    fits.PrimaryHDU(image, header=wcs.to_header()).writeto(buffer)
    payload = buffer.getvalue()

    fits_service = cast(FitsService, _FakeFitsService(payload))
    provider = _TrackingProvider(delay_s=0.5)
    service = GaiaVerificationService(
        detection_service=SourceDetectionService(fits=fits_service),
        fits=fits_service,
        provider=provider,
        query_timeout_s=30.0,
    )

    started = time.perf_counter()
    result = await service.verify_from_record(
        uuid4(),
        config=PointDetectionConfigSchema(sigma=6.0, fwhm=5.0),
        gaia_config=GaiaMatchConfigSchema(match_radius_arcsec=4.0),
    )
    elapsed = time.perf_counter() - started

    assert result.queried is True
    assert result.summary.point.count >= 8
    assert (
        len(provider.searches) == 9
    )  # 8 bloques + fallback single-query (paridad TPI gaia.py:183-204)
    assert provider.max_concurrent == 8
    assert all(radius >= 60.0 for _, _, radius in provider.searches)
    assert elapsed < 3.0


@pytest.mark.asyncio
async def test_verify_from_record_times_out_gracefully() -> None:
    payload = _wcs_fits_bytes()
    fits_service = cast(FitsService, _FakeFitsService(payload))
    service = GaiaVerificationService(
        detection_service=SourceDetectionService(fits=fits_service),
        fits=fits_service,
        provider=_SlowGaiaProvider(),
        query_timeout_s=0.05,
    )

    result = await service.verify_from_record(
        uuid4(),
        config=PointDetectionConfigSchema(sigma=6.0, fwhm=5.0),
    )

    assert result.queried is False
    assert result.error is not None
    assert "timed out" in result.error
    assert result.wcs_present is True
    assert result.matches
    assert all(row.gaia_match is False for row in result.matches)
    assert result.summary.point.count == len(result.matches)

    await asyncio.sleep(1.2)
