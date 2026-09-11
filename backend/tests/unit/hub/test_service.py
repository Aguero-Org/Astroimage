from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from uuid import uuid4

import numpy as np
import pytest
from astropy.io import fits

from astroimage.fits.model import FitsRecord
from astroimage.fits.schema import FitsRecordSummarySchema
from astroimage.hub.importer import HubbleNotFoundError, ImportedImage
from astroimage.hub.schema import FetchImageResponseSchema, ListRecordsResponseSchema
from astroimage.hub.service import HubbleImageService


def _sample_image() -> ImportedImage:
    data = np.ones((2, 3), dtype=float)
    buffer = BytesIO()
    fits.PrimaryHDU(data).writeto(buffer)
    return ImportedImage(
        payload=buffer.getvalue(),
        filename="hst_drz.fits",
        target_name="M31",
        ra_deg=10.684,
        dec_deg=41.269,
        observation_id="obs-1",
        proposal_id="10000",
        instrument="WFC3/UVIS",
    )


class _FakeImporter:
    def __init__(self, image: ImportedImage) -> None:
        self._image = image

    async def fetch_image(self, target_name: str) -> ImportedImage:
        return self._image


class _FakeFitsService:
    def __init__(self) -> None:
        self.stored: list[tuple[bytes, str, bool]] = []
        self._id = uuid4()
        self.records: list[FitsRecord] = []

    async def store_bytes(
        self,
        payload: bytes,
        *,
        source_name: str,
        hdu_index: int | None = None,
        analyze: bool = True,
    ) -> FitsRecord:
        self.stored.append((payload, source_name, analyze))

        return FitsRecord(
            id=self._id,
            object_key=f"fits/{self._id}.fits",
            original_filename=source_name,
            size_bytes=len(payload),
            created_at=datetime.now(UTC),
            metadata_payload={
                "source_name": source_name,
                "hdus": {"selected": 0},
            },
        )

    async def list_record_summaries(self, **kwargs: object) -> list[FitsRecordSummarySchema]:
        return [
            FitsRecordSummarySchema(record_id=record.id, name=record.original_filename)
            for record in self.records
        ]

    async def search_record_summaries(
        self,
        name: str,
        **kwargs: object,
    ) -> list[FitsRecordSummarySchema]:
        return [
            FitsRecordSummarySchema(record_id=record.id, name=record.original_filename)
            for record in self.records
            if name.lower() in record.original_filename.lower()
        ]


def _make_record(name: str) -> FitsRecord:
    return FitsRecord(
        id=uuid4(),
        object_key=f"fits/{uuid4()}.fits",
        original_filename=name,
        size_bytes=1024,
        created_at=datetime.now(UTC),
        metadata_payload={"source_name": name, "hdus": {"selected": 0}},
    )


async def test_service_fetches_image_and_returns_record_id() -> None:
    image = _sample_image()
    fits_service = _FakeFitsService()
    service = HubbleImageService(_FakeImporter(image), fits_service)  # type: ignore[arg-type]

    result = await service.fetch("M31")

    assert isinstance(result, FetchImageResponseSchema)
    assert result.record_id == fits_service._id
    assert fits_service.stored == [(image.payload, "M31", False)]
    assert len(result.model_dump()) == 1


async def test_service_propagates_not_found_error() -> None:
    class _EmptyImporter:
        async def fetch_image(self, target_name: str) -> ImportedImage:
            raise HubbleNotFoundError(f"No Hubble data found for {target_name!r}")

    service = HubbleImageService(_EmptyImporter(), _FakeFitsService())  # type: ignore[arg-type]

    with pytest.raises(HubbleNotFoundError):
        await service.fetch("unknown-object")


async def test_service_lists_records_as_summaries() -> None:
    fits_service = _FakeFitsService()
    fits_service.records = [_make_record("hst_drz.fits"), _make_record("hst_flt.fits")]
    service = HubbleImageService(_FakeImporter(_sample_image()), fits_service)  # type: ignore[arg-type]

    result = await service.list_records()

    assert isinstance(result, ListRecordsResponseSchema)
    assert [r.name for r in result.records] == ["hst_drz.fits", "hst_flt.fits"]


async def test_service_searches_records_by_name() -> None:
    fits_service = _FakeFitsService()
    fits_service.records = [
        _make_record("hst_m31_drz.fits"),
        _make_record("hst_ngc.fits"),
    ]
    service = HubbleImageService(_FakeImporter(_sample_image()), fits_service)  # type: ignore[arg-type]

    result = await service.search_records("m31")

    assert [r.name for r in result.records] == ["hst_m31_drz.fits"]
