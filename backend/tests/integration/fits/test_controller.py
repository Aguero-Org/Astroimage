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
    assert body["instrument"]["telescope"] == "VLT"
    assert body["instrument"]["instrument"] == "FORS2"
    assert body["instrument"]["filter_name"] == "B"
    assert body["instrument"]["exptime"] == 30.0
    assert body["image"]["shape"] == [5, 5]
    assert body["hdus"]["selected"] == 0
    assert body["hdus"]["image_indices"] == [0]
    assert "TELESCOP" in body["header"]
    assert "wcs" in body
    assert "photometry" in body
    assert "tables" in body


@pytest.mark.asyncio
async def test_extract_fits_metadata_rejects_empty(client: AsyncClient) -> None:
    response = await client.post(
        "/fits/metadata",
        files={"file": ("empty.fits", b"", "application/fits")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_import_fits_file_is_listed_without_mast_provenance(client: AsyncClient) -> None:
    payload = _sample_fits_bytes()
    response = await client.post(
        "/fits",
        files={"files": ("vlt.fits", payload, "application/fits")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body[0]["slug"] == "vlt.fits"
    listed = await client.get("/image")
    assert listed.status_code == 200
    match = next(
        item for item in listed.json()["records"] if item["record_id"] == body[0]["record_id"]
    )
    assert match["display_name"] == "vlt.fits"
    assert match["proposal_id"] is None
    assert match["data_uri"] is None
    assert match["instrument"] == "FORS2"

    duplicate = await client.post(
        "/fits",
        files={"files": ("copy.fits", payload, "application/fits")},
    )
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_download_imported_fits_file(client: AsyncClient) -> None:
    payload = _sample_fits_bytes().replace(b"VLT", b"HST")
    created = await client.post(
        "/fits",
        files={"files": ("vlt.fits", payload, "application/fits")},
    )
    assert created.status_code == 200
    record_id = created.json()[0]["record_id"]

    downloaded = await client.get(f"/fits/{record_id}/file")

    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "application/fits"
    assert downloaded.headers["content-disposition"] == 'attachment; filename="vlt.fits"'
    assert downloaded.content == payload


@pytest.mark.asyncio
async def test_import_fits_rejects_a_cube(client: AsyncClient) -> None:
    buffer = BytesIO()
    fits.PrimaryHDU(np.ones((2, 2, 2))).writeto(buffer)
    response = await client.post(
        "/fits",
        files={"files": ("cube.fits", buffer.getvalue(), "application/fits")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_import_fits_from_url(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _sample_fits_bytes()
    payload = payload.replace(b"FORS2", b"UVES ")

    async def _download(url: str, max_bytes: int) -> bytes:
        assert url == "https://example.test/folder/nebula.fits"
        assert max_bytes > len(payload)
        return payload

    monkeypatch.setattr("astroimage.fits.service._download_fits", _download)
    response = await client.post(
        "/fits/from-url",
        json={"url": "https://example.test/folder/nebula.fits"},
    )
    assert response.status_code == 200
    assert response.json()["slug"] == "nebula.fits"

    again = await client.post(
        "/fits/from-url",
        json={"url": "https://example.test/folder/nebula.fits"},
    )
    assert again.status_code == 409


@pytest.mark.asyncio
async def test_import_fits_from_url_rejects_a_relative_address(client: AsyncClient) -> None:
    response = await client.post("/fits/from-url", json={"url": "nebula.fits"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_extract_fits_metadata_rejects_garbage(client: AsyncClient) -> None:
    response = await client.post(
        "/fits/metadata",
        files={"file": ("bad.fits", b"not-a-fits-file", "application/octet-stream")},
    )
    assert response.status_code == 400
