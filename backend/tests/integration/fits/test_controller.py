from io import BytesIO

import numpy as np
import pytest
from astropy.io import fits
from httpx import AsyncClient


def _sample_fits_bytes() -> bytes:
    data = np.full((5, 5), 42.0)
    hdu = fits.PrimaryHDU(data)
    hdu.header["TELESCOP"] = "VLT"
    hdu.header["INSTRUME"] = "FORS2"
    hdu.header["FILTER1"] = "B"
    hdu.header["EXPTIME"] = 30.0
    buffer = BytesIO()
    hdu.writeto(buffer)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_extract_fits_metadata_upload(client: AsyncClient) -> None:
    payload = _sample_fits_bytes()
    response = await client.post(
        "/fits/metadata",
        files={"file": ("vlt.fits", payload, "application/fits")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source_name"] == "vlt.fits"
    assert body["telescope"] == "VLT"
    assert body["instrument"] == "FORS2"
    assert body["filter_name"] == "B"
    assert body["exptime"] == 30.0
    assert body["shape"] == [5, 5]
    assert body["hdu_index"] == 0
    assert "TELESCOP" in body["header"]


@pytest.mark.asyncio
async def test_extract_fits_metadata_rejects_empty(client: AsyncClient) -> None:
    response = await client.post(
        "/fits/metadata",
        files={"file": ("empty.fits", b"", "application/fits")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_extract_fits_metadata_rejects_garbage(client: AsyncClient) -> None:
    response = await client.post(
        "/fits/metadata",
        files={"file": ("bad.fits", b"not-a-fits-file", "application/octet-stream")},
    )
    assert response.status_code == 400
