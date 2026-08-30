from __future__ import annotations

from io import BytesIO

import numpy as np
import pytest
from astropy.io import fits
from httpx import AsyncClient

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _gradient_fits_bytes() -> bytes:
    image = np.linspace(0.0, 100.0, 256).reshape(16, 16)
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_render_fits_image_returns_png(client: AsyncClient) -> None:
    response = await client.post(
        "/render/image",
        files={"file": ("gradient.fits", _gradient_fits_bytes(), "application/fits")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(_PNG_SIGNATURE)


@pytest.mark.asyncio
async def test_render_fits_image_accepts_config_params(client: AsyncClient) -> None:
    response = await client.post(
        "/render/image",
        files={"file": ("gradient.fits", _gradient_fits_bytes(), "application/fits")},
        data={"stretch": "asinh", "pmin": "5.0", "pmax": "95.0", "gamma": "1.4"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_render_fits_image_rejects_empty(client: AsyncClient) -> None:
    response = await client.post(
        "/render/image",
        files={"file": ("empty.fits", b"", "application/fits")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_render_fits_image_rejects_garbage(client: AsyncClient) -> None:
    response = await client.post(
        "/render/image",
        files={"file": ("bad.fits", b"not-a-fits-file", "application/octet-stream")},
    )

    assert response.status_code == 400
