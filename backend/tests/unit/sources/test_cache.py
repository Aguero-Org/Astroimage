from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from astroimage.fits.model import FitsRecord
from astroimage.sources.cache import (
    CachedDetection,
    DetectionCache,
    detection_cache_key,
    detection_scope_key,
)
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


def _entry(name: str, config: PointDetectionConfigSchema | None = None) -> CachedDetection:
    return CachedDetection(
        result=SourceDetectionResult(source_name=name),
        point_config=config or PointDetectionConfigSchema(),
        extended_config=ExtendedDetectionConfigSchema(),
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


def test_scope_key_ignores_the_detection_parameters() -> None:
    record_id = uuid4()
    base: dict[str, Any] = {"record_id": record_id, "client_id": "alice", "hdu_index": None}

    assert detection_scope_key(**base) == detection_scope_key(**base)
    assert detection_scope_key(**{**base, "client_id": "bob"}) != detection_scope_key(**base)
    assert detection_scope_key(**{**base, "record_id": uuid4()}) != detection_scope_key(**base)
    assert detection_scope_key(**{**base, "hdu_index": 1}) != detection_scope_key(**base)


def test_cache_evicts_least_recently_used() -> None:
    cache = DetectionCache(max_entries=2)
    first = _entry("a")
    second = _entry("b")
    third = _entry("c")

    cache.set("a", first, scope="sa")
    cache.set("b", second, scope="sb")
    cache.get("a")
    cache.set("c", third, scope="sc")

    assert cache.get("a") is first
    assert cache.get("b") is None
    assert cache.get("c") is third


def test_cache_returns_the_most_recent_detection_of_a_scope() -> None:
    cache = DetectionCache()
    record_id = uuid4()
    scope = detection_scope_key(record_id=record_id, client_id="alice", hdu_index=None)
    tuned = PointDetectionConfigSchema(fwhm=9.0)

    cache.set("key-1", _entry("first"), scope=scope)
    cache.set("key-2", _entry("second", tuned), scope=scope)

    latest = cache.get_latest(scope)
    assert latest is not None
    assert latest.result.source_name == "second"
    assert latest.point_config.fwhm == 9.0


def test_cache_keeps_the_config_that_produced_the_detection() -> None:
    cache = DetectionCache()
    config = PointDetectionConfigSchema(sigma=7.5)
    extended = ExtendedDetectionConfigSchema(max_sources=4)

    cache.set(
        "key",
        CachedDetection(
            result=SourceDetectionResult(source_name="a"),
            point_config=config,
            extended_config=extended,
        ),
        scope="scope",
    )

    entry = cache.get("key")
    assert entry is not None
    assert entry.point_config is config
    assert entry.extended_config is extended


def test_cache_scopes_are_isolated_per_client() -> None:
    cache = DetectionCache()
    record_id = uuid4()
    alice = detection_scope_key(record_id=record_id, client_id="alice", hdu_index=None)
    bob = detection_scope_key(record_id=record_id, client_id="bob", hdu_index=None)

    cache.set("key-alice", _entry("alice"), scope=alice)

    assert cache.get_latest(bob) is None
    assert cache.get_latest(alice) is not None


def test_cache_returns_nothing_for_an_unknown_scope() -> None:
    assert DetectionCache().get_latest("never-stored") is None


def test_cache_forgets_a_scope_whose_entry_was_evicted() -> None:
    cache = DetectionCache(max_entries=1)
    scope = detection_scope_key(record_id=uuid4(), client_id="alice", hdu_index=None)

    cache.set("key-1", _entry("first"), scope=scope)
    cache.set("key-2", _entry("second"), scope="other-scope")

    assert cache.get_latest(scope) is None


def test_cache_clears_entries_and_scopes() -> None:
    cache = DetectionCache()
    cache.set("key", _entry("a"), scope="scope")

    cache.clear()

    assert cache.get("key") is None
    assert cache.get_latest("scope") is None


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
