from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from astroimage.fits.model import FitsRecord
from astroimage.sources.cache import DetectionCache, detection_cache_key
from astroimage.sources.model import SourceDetectionResult
from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    PointDetectionConfigSchema,
)
from astroimage.sources.service import SourceDetectionService
from tests.unit.sources.helpers import (
    fits_bytes_from_image,
    synthetic_point_source_image,
)


def test_cache_key_distinguishes_record_client_and_params() -> None:
    record_id = uuid4()
    config = PointDetectionConfigSchema(sigma=6.0)
    extended = ExtendedDetectionConfigSchema()
    base_kwargs: dict[str, Any] = {
        "record_id": record_id,
        "client_id": "alice",
        "hdu_index": None,
        "config": config,
        "extended_config": extended,
    }

    assert detection_cache_key(**base_kwargs) == detection_cache_key(**base_kwargs)
    assert detection_cache_key(
        **{**base_kwargs, "client_id": "bob"},
    ) != detection_cache_key(**base_kwargs)
    assert detection_cache_key(
        **{**base_kwargs, "record_id": uuid4()},
    ) != detection_cache_key(**base_kwargs)
    assert detection_cache_key(
        **{**base_kwargs, "config": PointDetectionConfigSchema(sigma=8.0)},
    ) != detection_cache_key(**base_kwargs)
    assert detection_cache_key(
        **{**base_kwargs, "hdu_index": 2},
    ) != detection_cache_key(**base_kwargs)


def test_cache_evicts_least_recently_used() -> None:
    cache = DetectionCache(max_entries=2)
    first = SourceDetectionResult(source_name="a")
    second = SourceDetectionResult(source_name="b")
    third = SourceDetectionResult(source_name="c")

    cache.set("a", first)
    cache.set("b", second)
    cache.get("a")
    cache.set("c", third)

    assert cache.get("a") is first
    assert cache.get("b") is None
    assert cache.get("c") is third


class _CountingFitsService:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.payload_fetches = 0
        self.record = FitsRecord(
            id=uuid4(),
            object_key="fits/record-uuid.fits",
            original_filename="survey.fits",
            size_bytes=len(payload),
            created_at=datetime.now(UTC),
            metadata_payload={},
        )

    async def get_record(self, record_id: object) -> FitsRecord:
        return self.record

    async def get_payload(self, record: object) -> bytes:
        self.payload_fetches += 1
        return self.payload

    async def update_record_metadata(
        self,
        record: object,
        payload: object,
        *,
        hdu_index: object = None,
    ) -> FitsRecord:
        return self.record


async def test_resolve_caches_detection_per_client_and_params() -> None:
    image, _ = synthetic_point_source_image()
    payload = fits_bytes_from_image(image)
    fits_service = _CountingFitsService(payload)
    service = SourceDetectionService(fits=fits_service)  # type: ignore[arg-type]
    config = PointDetectionConfigSchema(sigma=6.0, fwhm=5.0)
    record_id = uuid4()

    first = await service.resolve_detection_from_record(
        record_id,
        client_id="alice",
        config=config,
    )
    second = await service.resolve_detection_from_record(
        record_id,
        client_id="alice",
        config=config,
    )
    other_client = await service.resolve_detection_from_record(
        record_id,
        client_id="bob",
        config=config,
    )

    assert first is second
    assert first is not other_client
    assert fits_service.payload_fetches == 2
