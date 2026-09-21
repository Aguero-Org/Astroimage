from __future__ import annotations

from io import BytesIO
from uuid import uuid4

import numpy as np
import pytest
from astropy.io import fits
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.service import FitsService
from tests.unit.sources.helpers import (
    synthetic_extended_source_image,
    synthetic_point_source_image,
)


def _sources_fits_bytes() -> bytes:
    image, _ = synthetic_point_source_image()
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()


async def _store_sources(
    fits_service: FitsService,
    db_session: AsyncSession,
) -> str:
    record = await fits_service.store_bytes(_sources_fits_bytes(), source_name="survey.fits")
    await db_session.commit()
    return str(record.id)


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
