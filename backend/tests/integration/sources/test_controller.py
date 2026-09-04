from __future__ import annotations

from io import BytesIO
from uuid import uuid4

import numpy as np
import pytest
from astropy.io import fits
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.service import FitsService
from tests.unit.sources.helpers import synthetic_point_source_image


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
    assert body["summary"]["extended_count"] == 0
    assert body["summary"]["point_count"] == len(body["point_sources"])
    assert body["summary"]["point_count"] >= 3
    assert body["extended_sources"] == []
    for source in body["point_sources"]:
        assert source["object_type"] == "point"
        assert source["xcentroid"] > 0
        assert source["ycentroid"] > 0
        assert source["snr"] >= 4.0
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
async def test_detect_sources_ignores_nan_border(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    image, _ = synthetic_point_source_image()
    image[:60, :] = np.nan
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="border.fits")
    await db_session.commit()

    response = await client.get(
        f"/image/{record.id}/sources",
        params={"fwhm": "5.0", "sigma": "6.0"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["point_count"] >= 2
    assert all(source["ycentroid"] >= 60 for source in body["point_sources"])
    assert any(
        abs(source["xcentroid"] - 60.5) < 3.0 and abs(source["ycentroid"] - 70.5) < 3.0
        for source in body["point_sources"]
    )


@pytest.mark.asyncio
async def test_detect_sources_returns_extended_sources(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    image, _ = synthetic_point_source_image(size=600)
    coordinate_y, coordinate_x = np.mgrid[0:600, 0:600]
    cosine = np.cos(np.deg2rad(45.0))
    sine = np.sin(np.deg2rad(45.0))
    delta_x = coordinate_x - 300.0
    delta_y = coordinate_y - 300.0
    axis_x = cosine * delta_x + sine * delta_y
    axis_y = -sine * delta_x + cosine * delta_y
    bivariate = (axis_x / 14.0) ** 2 + (axis_y / 3.0) ** 2
    image = image + 12000.0 * np.exp(-0.5 * bivariate)
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    record = await fits_service.store_bytes(buffer.getvalue(), source_name="extended.fits")
    await db_session.commit()

    response = await client.get(
        f"/image/{record.id}/sources",
        params={
            "fwhm": "5.0",
            "sigma": "6.0",
            "extended_min_snr": "100.0",
            "extended_max_sources": "20",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["extended_count"] == len(body["extended_sources"])
    assert any(
        abs(source["xcentroid"] - 300.0) < 8.0
        and abs(source["ycentroid"] - 300.0) < 8.0
        and source["object_type"] == "extended"
        for source in body["extended_sources"]
    )
    ranks = [source["rank"] for source in body["extended_sources"]]
    assert ranks == list(range(1, len(ranks) + 1))
