from __future__ import annotations

from io import BytesIO
from typing import Any, cast
from uuid import uuid4

import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.unit.sources.helpers import synthetic_point_source_image

from astroimage.fits.service import FitsService
from astroimage.main import app
from astroimage.simbad.deps import simbad_provider_dependency
from astroimage.simbad.model import SimbadAlias, SimbadObject, SimbadReference
from astroimage.simbad.provider import SimbadCatalogProvider


def _wcs_point_source_fits_bytes() -> bytes:
    image, _ = synthetic_point_source_image(positions=((127.5, 127.5),))
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
    def __init__(self, *, error: Exception | None = None) -> None:
        self._error = error
        self.region_calls = 0

    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
        object_type: str | None = None,
    ) -> list[SimbadObject]:
        self.region_calls += 1
        assert center.ra.deg == pytest.approx(10.0, abs=0.01)
        assert center.dec.deg == pytest.approx(20.0, abs=0.01)
        assert radius_arcsec >= 60.0
        assert row_limit in {10, 25}
        assert object_type is None
        if self._error is not None:
            raise self._error
        return [
            SimbadObject(
                main_id="M   1",
                ra_deg=10.0,
                dec_deg=20.0,
                separation_arcsec=0.0,
                otype="SNR",
                otype_text="SuperNova Remnant",
                reference_count=6602,
            )
        ]

    def query_aliases(self, main_ids: list[str], *, max_records: int) -> list[SimbadAlias]:
        assert main_ids == ["M   1"]
        assert max_records > 0
        return [
            SimbadAlias(object_id="M   1", name="M 1"),
            SimbadAlias(object_id="M   1", name="Gaia DR3 123456"),
        ]

    def query_references(
        self,
        main_ids: list[str],
        *,
        max_records: int,
    ) -> list[SimbadReference]:
        assert main_ids == ["M   1"]
        assert max_records > 0
        return [
            SimbadReference(
                object_id="M   1",
                bibcode="2024A&A...2B",
                year=2024,
                doi="10.1000/example",
            )
        ]


async def _store_record(
    fits_service: FitsService,
    db_session: AsyncSession,
    payload: bytes,
) -> str:
    record = await fits_service.store_bytes(payload, source_name="survey.fits")
    await db_session.commit()
    return str(record.id)


@pytest.mark.asyncio
async def test_simbad_references_returns_objects_and_bibliography(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_record(fits_service, db_session, _wcs_point_source_fits_bytes())
    provider = _RecordingProvider()
    app.dependency_overrides[simbad_provider_dependency] = lambda: cast(
        SimbadCatalogProvider, provider
    )
    try:
        response = await client.get(
            f"/image/{record_id}/simbad-references",
            params={"limit": "10", "max_references": "1"},
            headers={"X-Client-Id": "alice"},
        )
    finally:
        app.dependency_overrides.pop(simbad_provider_dependency, None)

    assert response.status_code == 200
    body = cast(dict[str, Any], response.json())
    assert body["wcs_present"] is True
    assert body["queried"] is True
    assert body["error"] is None
    assert body["summary"]["object_count"] == 1
    assert body["summary"]["reference_count"] == 1
    assert provider.region_calls == 1

    obj = body["objects"][0]
    assert obj["main_id"] == "M   1"
    assert obj["gaia_source_id"] == "123456"
    assert obj["references"][0]["bibcode"] == "2024A&A...2B"
    assert obj["image_match"] is not None
    assert obj["image_match"]["matched"] is True


@pytest.mark.asyncio
async def test_simbad_references_without_wcs_skips_query(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_record(fits_service, db_session, _plain_fits_bytes())
    provider = _RecordingProvider()
    app.dependency_overrides[simbad_provider_dependency] = lambda: cast(
        SimbadCatalogProvider, provider
    )
    try:
        response = await client.get(f"/image/{record_id}/simbad-references")
    finally:
        app.dependency_overrides.pop(simbad_provider_dependency, None)

    assert response.status_code == 200
    body = cast(dict[str, Any], response.json())
    assert body["wcs_present"] is False
    assert body["queried"] is False
    assert body["objects"] == []
    assert provider.region_calls == 0


@pytest.mark.asyncio
async def test_simbad_references_surfaces_provider_error(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_record(fits_service, db_session, _wcs_point_source_fits_bytes())
    provider = _RecordingProvider(error=RuntimeError("tap down"))
    app.dependency_overrides[simbad_provider_dependency] = lambda: cast(
        SimbadCatalogProvider, provider
    )
    try:
        response = await client.get(f"/image/{record_id}/simbad-references")
    finally:
        app.dependency_overrides.pop(simbad_provider_dependency, None)

    assert response.status_code == 200
    body = cast(dict[str, Any], response.json())
    assert body["queried"] is False
    assert "tap down" in body["error"]


@pytest.mark.asyncio
async def test_simbad_references_caches_per_client(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record_id = await _store_record(fits_service, db_session, _wcs_point_source_fits_bytes())
    provider = _RecordingProvider()
    app.dependency_overrides[simbad_provider_dependency] = lambda: cast(
        SimbadCatalogProvider, provider
    )
    try:
        first = await client.get(
            f"/image/{record_id}/simbad-references",
            params={"limit": "10"},
            headers={"X-Client-Id": "alice"},
        )
        second = await client.get(
            f"/image/{record_id}/simbad-references",
            params={"limit": "10"},
            headers={"X-Client-Id": "alice"},
        )
    finally:
        app.dependency_overrides.pop(simbad_provider_dependency, None)

    assert first.status_code == 200
    assert first.json() == second.json()
    assert provider.region_calls == 1


@pytest.mark.asyncio
async def test_simbad_references_rejects_invalid_object_type(client: AsyncClient) -> None:
    response = await client.get(
        f"/image/{uuid4()}/simbad-references",
        params={"object_type": "SNR' OR 1=1"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_simbad_references_missing_record_returns_not_found(client: AsyncClient) -> None:
    provider = _RecordingProvider()
    app.dependency_overrides[simbad_provider_dependency] = lambda: cast(
        SimbadCatalogProvider, provider
    )
    try:
        response = await client.get(f"/image/{uuid4()}/simbad-references")
    finally:
        app.dependency_overrides.pop(simbad_provider_dependency, None)

    assert response.status_code == 404
    assert provider.region_calls == 0
