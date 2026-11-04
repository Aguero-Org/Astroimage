from __future__ import annotations

import io
from uuid import UUID, uuid4

import numpy as np
import pytest
from astropy.io import fits

from astroimage.fits.reader import FitsReader
from astroimage.render.model import ImagePreview
from astroimage.render.png import thumbnail_png
from astroimage.render.preview import (
    EQUILIBRIO,
    PRESET_ID,
    PreviewService,
    preview_config_hash,
    preview_object_key,
)
from astroimage.render.service import render_png_bytes
from astroimage.shared.background import BackgroundTasks
from astroimage.shared.errors import BadRequestError

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _gradient_fits_bytes() -> bytes:
    image = np.linspace(0.0, 100.0, 64).reshape(8, 8)
    buffer = io.BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()


class _MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.puts = 0

    async def put_bytes(self, object_key: str, payload: bytes, *, content_type: str) -> None:
        del content_type
        self.puts += 1
        self.objects[object_key] = payload

    async def get_bytes(self, object_key: str) -> bytes:
        try:
            return self.objects[object_key]
        except KeyError as exc:
            raise LookupError(object_key) from exc

    async def remove(self, object_key: str) -> None:
        self.objects.pop(object_key, None)

    async def list_object_keys(self, prefix: str) -> list[str]:
        return [key for key in self.objects if key.startswith(prefix)]


class _MemorySession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class _Scope:
    def __init__(self, session: _MemorySession) -> None:
        self._session = session

    async def __aenter__(self) -> _MemorySession:
        return self._session

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None


class _Repository:
    def __init__(self) -> None:
        self.rows: dict[tuple[object, str, int], ImagePreview] = {}

    async def find(
        self,
        record_id: object,
        preset_id: str,
        edge_px: int,
    ) -> ImagePreview | None:
        return self.rows.get((record_id, preset_id, edge_px))

    async def save(self, preview: ImagePreview) -> ImagePreview:
        self.rows[(preview.record_id, preview.preset_id, preview.edge_px)] = preview
        return preview


class _Fits:
    def __init__(self, payload: bytes, record_ids: list[object] | None = None) -> None:
        self.payload = payload
        self.record_ids = record_ids or []
        self.reads = 0
        self.fail_ids: set[object] = set()

    async def get_record(self, record_id: object) -> object:
        if record_id in self.fail_ids:
            raise RuntimeError(f"broken {record_id}")
        return object()

    async def get_payload(self, record: object) -> bytes:
        del record
        self.reads += 1
        return self.payload

    async def list_record_ids(self) -> list[object]:
        return list(self.record_ids)


def _service(
    fits: _Fits | None = None,
    storage: _MemoryStorage | None = None,
    repository: _Repository | None = None,
    session: _MemorySession | None = None,
) -> tuple[PreviewService, _Fits, _MemoryStorage, _Repository, _MemorySession]:
    source = fits or _Fits(_gradient_fits_bytes())
    objects = storage or _MemoryStorage()
    store = repository or _Repository()
    db_session = session or _MemorySession()

    def open_session() -> _Scope:
        return _Scope(db_session)

    service = PreviewService(
        BackgroundTasks(),
        open_session,
        objects,
        session=db_session,
        reader=FitsReader(),
        fits=source,  # type: ignore[arg-type]
        fits_factory=lambda _session: source,
        repository_factory=lambda _session: store,
    )
    return service, source, objects, store, db_session


def _seed(
    store: _Repository,
    objects: _MemoryStorage,
    record_id: UUID,
    edge: int,
    png: bytes,
) -> None:
    key = preview_object_key(record_id, PRESET_ID, edge)
    objects.objects[key] = png
    store.rows[(record_id, PRESET_ID, edge)] = ImagePreview(
        record_id=record_id,
        preset_id=PRESET_ID,
        edge_px=edge,
        config_hash=preview_config_hash(PRESET_ID, edge, EQUILIBRIO),
        object_key=key,
    )


def test_equilibrio_matches_the_frontend_default_preset() -> None:
    assert EQUILIBRIO.stretch == "linear"
    assert EQUILIBRIO.limits == "percentiles"
    assert EQUILIBRIO.colormap == "grey"
    assert EQUILIBRIO.pmin == 1.0
    assert EQUILIBRIO.pmax == 99.0
    assert EQUILIBRIO.gamma == 0.5


async def test_png_rejects_an_unknown_size_without_reading() -> None:
    service, source, objects, _store, _session = _service()

    with pytest.raises(BadRequestError, match="Preview size is not available"):
        await service.png(uuid4(), 100)

    assert source.reads == 0
    assert objects.puts == 0


async def test_png_returns_the_stored_object_without_rendering() -> None:
    record_id = uuid4()
    service, source, objects, store, _session = _service()
    _seed(store, objects, record_id, 256, b"stored-png")

    png = await service.png(record_id, 256)

    assert png == b"stored-png"
    assert source.reads == 0
    assert objects.puts == 0


async def test_png_live_renders_when_the_row_is_missing_and_does_not_write() -> None:
    record_id = uuid4()
    service, source, objects, store, session = _service()

    png = await service.png(record_id, 256)

    expected = thumbnail_png(
        render_png_bytes(FitsReader(), source.payload, EQUILIBRIO),
        256,
    )
    assert png == expected
    assert png.startswith(_PNG_SIGNATURE)
    assert objects.puts == 0
    assert store.rows == {}
    assert session.commits == 0


async def test_png_live_renders_when_the_object_is_missing_and_does_not_write() -> None:
    record_id = uuid4()
    service, source, objects, store, _session = _service()
    _seed(store, objects, record_id, 256, b"gone")
    objects.objects.clear()

    png = await service.png(record_id, 256)

    assert png.startswith(_PNG_SIGNATURE)
    assert source.reads == 1
    assert objects.puts == 0


async def test_png_ignores_a_stale_hash_and_does_not_write() -> None:
    record_id = uuid4()
    service, _source, objects, store, _session = _service()
    key = preview_object_key(record_id, PRESET_ID, 256)
    objects.objects[key] = b"old-preset"
    store.rows[(record_id, PRESET_ID, 256)] = ImagePreview(
        record_id=record_id,
        preset_id=PRESET_ID,
        edge_px=256,
        config_hash="stale",
        object_key=key,
    )

    png = await service.png(record_id, 256)

    assert png != b"old-preset"
    assert objects.puts == 0
    assert store.rows[(record_id, PRESET_ID, 256)].config_hash == "stale"


async def test_render_stored_skips_work_when_every_edge_is_current() -> None:
    record_id = uuid4()
    service, source, objects, store, session = _service()
    for edge in (256, 512, 1024):
        _seed(store, objects, record_id, edge, f"edge-{edge}".encode())
    objects.puts = 0

    await service.render_stored(record_id)

    assert source.reads == 0
    assert objects.puts == 0
    assert session.commits == 0


async def test_render_stored_writes_missing_edges_and_keeps_current_ones() -> None:
    record_id = uuid4()
    service, source, objects, store, session = _service()
    _seed(store, objects, record_id, 256, b"keep-me")
    objects.puts = 0

    await service.render_stored(record_id)

    assert source.reads == 1
    assert objects.puts == 2
    assert objects.objects[preview_object_key(record_id, PRESET_ID, 256)] == b"keep-me"
    assert session.commits == 1
    assert set(store.rows) == {
        (record_id, PRESET_ID, 256),
        (record_id, PRESET_ID, 512),
        (record_id, PRESET_ID, 1024),
    }


async def test_render_stored_rewrites_a_row_whose_object_is_missing() -> None:
    record_id = uuid4()
    service, _source, objects, store, session = _service()
    for edge in (256, 512, 1024):
        _seed(store, objects, record_id, edge, b"present")
    missing_key = preview_object_key(record_id, PRESET_ID, 512)
    del objects.objects[missing_key]
    objects.puts = 0

    await service.render_stored(record_id)

    assert objects.puts == 1
    assert missing_key in objects.objects
    assert session.commits == 1


async def test_render_stored_is_idempotent() -> None:
    record_id = uuid4()
    service, source, objects, store, _session = _service()

    await service.render_stored(record_id)
    await service.render_stored(record_id)

    assert source.reads == 1
    assert len(store.rows) == 3
    assert objects.puts == 3


async def test_background_run_swallows_a_render_failure() -> None:
    record_id = uuid4()
    source = _Fits(_gradient_fits_bytes())
    source.fail_ids.add(record_id)
    service, _source, _objects, store, _session = _service(fits=source)

    await service._run(record_id)
    service.schedule(record_id)
    await service._tasks._tasks[f"preview:{record_id}"]

    assert store.rows == {}


async def test_render_stored_propagates_the_failure() -> None:
    record_id = uuid4()
    source = _Fits(_gradient_fits_bytes())
    source.fail_ids.add(record_id)
    service, *_rest = _service(fits=source)

    with pytest.raises(RuntimeError, match="broken"):
        await service.render_stored(record_id)


async def test_backfill_continues_after_one_record_fails() -> None:
    broken = uuid4()
    healthy = uuid4()
    source = _Fits(_gradient_fits_bytes(), [broken, healthy])
    source.fail_ids.add(broken)
    service, _source, objects, store, _session = _service(fits=source)

    await service.backfill_missing()

    assert (broken, PRESET_ID, 256) not in store.rows
    assert (healthy, PRESET_ID, 256) in store.rows
    assert objects.puts == 3


async def test_backfill_swallows_a_listing_failure() -> None:
    class _BrokenFits(_Fits):
        async def list_record_ids(self) -> list[object]:
            raise RuntimeError("database down")

    service, *_rest = _service(fits=_BrokenFits(b""))

    await service.backfill_missing()


async def test_png_requires_a_request_binding() -> None:
    service, *_rest = _service()
    scheduler = PreviewService(service._tasks, service._session_factory, service._storage)

    with pytest.raises(TypeError, match="Preview read is not configured"):
        await scheduler.png(uuid4(), 256)
