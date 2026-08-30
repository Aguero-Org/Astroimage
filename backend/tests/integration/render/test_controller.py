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


def _gradient_files() -> dict[str, tuple[str, bytes, str]]:
    return {"file": ("gradient.fits", _gradient_fits_bytes(), "application/fits")}


@pytest.mark.asyncio
async def test_render_fits_image_returns_png(client: AsyncClient) -> None:
    response = await client.post("/render/image", files=_gradient_files())

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(_PNG_SIGNATURE)


@pytest.mark.asyncio
async def test_render_fits_image_accepts_config_params(client: AsyncClient) -> None:
    response = await client.post(
        "/render/image",
        files=_gradient_files(),
        data={"stretch": "asinh", "pmin": "5.0", "pmax": "95.0", "gamma": "1.4"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_render_fits_image_accepts_linear_stretch_and_zscale_limits(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/render/image",
        files=_gradient_files(),
        data={"stretch": "linear", "limits": "zscale"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


@pytest.mark.parametrize("colormap", ["inverse", "heat", "rainbow", "cube_helix"])
@pytest.mark.asyncio
async def test_render_fits_image_accepts_colormaps(client: AsyncClient, colormap: str) -> None:
    response = await client.post(
        "/render/image",
        files=_gradient_files(),
        data={"colormap": colormap},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_render_fits_image_rejects_unknown_stretch(client: AsyncClient) -> None:
    response = await client.post(
        "/render/image",
        files=_gradient_files(),
        data={"stretch": "exp"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_render_fits_image_rejects_unknown_limits(client: AsyncClient) -> None:
    response = await client.post(
        "/render/image",
        files=_gradient_files(),
        data={"limits": "minmax"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_render_fits_image_rejects_unknown_colormap(client: AsyncClient) -> None:
    response = await client.post(
        "/render/image",
        files=_gradient_files(),
        data={"colormap": "magma"},
    )

    assert response.status_code == 422


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


@pytest.mark.asyncio
async def test_render_fits_histogram_returns_bin_stats(client: AsyncClient) -> None:
    response = await client.post("/render/histogram", files=_gradient_files(), data={"bins": "32"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    payload = response.json()
    assert len(payload["bin_centers"]) == 32
    assert len(payload["counts"]) == 32
    assert sum(payload["counts"]) == 16 * 16
    assert payload["minimum"] <= payload["maximum"]


@pytest.mark.asyncio
async def test_render_fits_histogram_uses_default_bins(client: AsyncClient) -> None:
    response = await client.post("/render/histogram", files=_gradient_files())

    assert response.status_code == 200
    assert len(response.json()["counts"]) == 256


@pytest.mark.asyncio
async def test_render_fits_histogram_rejects_invalid_bins(client: AsyncClient) -> None:
    response = await client.post(
        "/render/histogram",
        files=_gradient_files(),
        data={"bins": "4097"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_render_fits_histogram_rejects_garbage(client: AsyncClient) -> None:
    response = await client.post(
        "/render/histogram",
        files={"file": ("bad.fits", b"not-a-fits-file", "application/octet-stream")},
    )

    assert response.status_code == 400
