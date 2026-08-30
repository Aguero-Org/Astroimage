from __future__ import annotations

from io import BytesIO

import numpy as np
import pytest
from astropy.io import fits
from httpx import AsyncClient

from tests.unit.sources.helpers import synthetic_point_source_image


def _sources_fits_bytes() -> bytes:
    image, _ = synthetic_point_source_image()
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_detect_sources_returns_point_sources(client: AsyncClient) -> None:
    payload = _sources_fits_bytes()
    response = await client.post(
        "/sources/detect",
        files={"file": ("survey.fits", payload, "application/fits")},
        data={
            "fwhm": "5.0",
            "sigma": "6.0",
            "min_snr": "4.0",
        },
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
async def test_detect_sources_with_max_sources_limit(client: AsyncClient) -> None:
    payload = _sources_fits_bytes()
    response = await client.post(
        "/sources/detect",
        files={"file": ("survey.fits", payload, "application/fits")},
        data={"fwhm": "5.0", "sigma": "6.0", "max_sources": "2"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["point_count"] <= 2


@pytest.mark.asyncio
async def test_detect_sources_rejects_garbage(client: AsyncClient) -> None:
    response = await client.post(
        "/sources/detect",
        files={"file": ("bad.fits", b"not-a-fits-file", "application/octet-stream")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_detect_sources_rejects_empty(client: AsyncClient) -> None:
    response = await client.post(
        "/sources/detect",
        files={"file": ("empty.fits", b"", "application/fits")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_detect_sources_noise_only_returns_no_sources(client: AsyncClient) -> None:
    rng = np.random.default_rng(3)
    image = rng.normal(scale=5.0, size=(128, 128))
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    response = await client.post(
        "/sources/detect",
        files={"file": ("noise.fits", buffer.getvalue(), "application/fits")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["point_count"] == 0


@pytest.mark.asyncio
async def test_detect_sources_constant_image_raises_bad_request(client: AsyncClient) -> None:
    buffer = BytesIO()
    fits.PrimaryHDU(np.zeros((128, 128))).writeto(buffer)
    response = await client.post(
        "/sources/detect",
        files={"file": ("flat.fits", buffer.getvalue(), "application/fits")},
    )
    assert response.status_code == 400
