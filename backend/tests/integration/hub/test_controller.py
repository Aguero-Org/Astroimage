from __future__ import annotations

from io import BytesIO
from uuid import UUID, uuid4

import numpy as np
from astropy.io import fits
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.service import FitsService
from astroimage.hub.deps import hubble_service_dependency
from astroimage.hub.importer import HubbleImporter, HubbleNotFoundError
from astroimage.hub.schema import (
    FetchImageResponseSchema,
    ListRecordsResponseSchema,
)
from astroimage.hub.service import HubbleImageService
from astroimage.main import app


def _record_id() -> UUID:
    return uuid4()


def _sample_fits_bytes() -> bytes:
    data = np.full((5, 5), 42.0)
    hdu = fits.PrimaryHDU(data)
    hdu.header["TELESCOP"] = "VLT"
    buffer = BytesIO()
    hdu.writeto(buffer)
    return buffer.getvalue()


def _real_service(fits_service: FitsService) -> HubbleImageService:
    return HubbleImageService(HubbleImporter(), fits_service)


class _FakeService:
    def __init__(
        self,
        result: FetchImageResponseSchema,
        error: Exception | None = None,
        records: ListRecordsResponseSchema | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self._records = records or ListRecordsResponseSchema(records=[])

    async def fetch(self, target_name: str) -> FetchImageResponseSchema:
        if self._error is not None:
            raise self._error
        return self._result

    async def list_records(self, **kwargs: object) -> ListRecordsResponseSchema:
        return self._records

    async def search_records(self, name: str, **kwargs: object) -> ListRecordsResponseSchema:
        return self._records


async def test_get_image_info_returns_stored_metadata(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    record = await fits_service.store_bytes(_sample_fits_bytes(), source_name="vlt.fits")
    await db_session.commit()

    app.dependency_overrides[hubble_service_dependency] = lambda: _real_service(fits_service)
    try:
        response = await client.get(f"/image/{record.id}/info")
    finally:
        app.dependency_overrides.pop(hubble_service_dependency, None)

    assert response.status_code == 200
    body = response.json()
    assert body["source_name"] == "vlt.fits"
    assert body["instrument"]["telescope"] == "VLT"
    assert body["hdus"]["selected"] == 0
    assert body["hdus"]["image_indices"] == [0]
    assert len(body["hdus"]["images"]) == 1
    detail = body["hdus"]["images"][0]
    assert detail["index"] == 0
    assert detail["shape"] == [5, 5]


async def test_get_image_info_missing_record(
    client: AsyncClient,
    fits_service: FitsService,
    db_session: AsyncSession,
) -> None:
    app.dependency_overrides[hubble_service_dependency] = lambda: _real_service(fits_service)
    try:
        response = await client.get(f"/image/{'0' * 32}/info")
    finally:
        app.dependency_overrides.pop(hubble_service_dependency, None)

    assert response.status_code == 404


async def test_list_astro_images_returns_all_records(client: AsyncClient) -> None:
    records = ListRecordsResponseSchema(
        records=[
            {"record_id": _record_id(), "name": "hst_drz.fits"},
            {"record_id": _record_id(), "name": "hst_flt.fits"},
        ]
    )
    fake = _FakeService(
        FetchImageResponseSchema(record_id=_record_id()),
        records=records,
    )
    app.dependency_overrides[hubble_service_dependency] = lambda: fake
    try:
        response = await client.get("/image")
    finally:
        app.dependency_overrides.pop(hubble_service_dependency, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "records": [{"record_id": str(r.record_id), "name": r.name} for r in records.records]
    }


async def test_search_astro_images_by_name_returns_filtered_records(
    client: AsyncClient,
) -> None:
    records = ListRecordsResponseSchema(
        records=[{"record_id": _record_id(), "name": "hst_m31.fits"}]
    )
    fake = _FakeService(
        FetchImageResponseSchema(record_id=_record_id()),
        records=records,
    )
    app.dependency_overrides[hubble_service_dependency] = lambda: fake
    try:
        response = await client.get("/image", params={"cuerpo_celeste": "m31"})
    finally:
        app.dependency_overrides.pop(hubble_service_dependency, None)

    assert response.status_code == 200
    assert "records" in response.json()


async def test_fetch_astro_image_returns_fits(client: AsyncClient) -> None:
    fake = _FakeService(
        FetchImageResponseSchema(
            record_id=_record_id(),
        )
    )
    app.dependency_overrides[hubble_service_dependency] = lambda: fake
    try:
        response = await client.get("/image/search", params={"query": "M31"})
    finally:
        app.dependency_overrides.pop(hubble_service_dependency, None)

    assert response.status_code == 200
    payload = response.json()
    assert "record_id" in payload
    assert payload["record_id"]
    assert len(payload) == 1


async def test_fetch_astro_image_requires_query_param(client: AsyncClient) -> None:
    response = await client.get("/image/search")

    assert response.status_code == 422


async def test_fetch_astro_image_not_found(client: AsyncClient) -> None:
    error = HubbleNotFoundError("No Hubble data found for celestial body 'unknown'")
    fake = _FakeService(
        FetchImageResponseSchema(
            record_id=_record_id(),
        ),
        error=error,
    )
    app.dependency_overrides[hubble_service_dependency] = lambda: fake
    try:
        response = await client.get("/image/search", params={"query": "unknown"})
    finally:
        app.dependency_overrides.pop(hubble_service_dependency, None)

    assert response.status_code == 404
    assert "unknown" in response.json()["detail"]
