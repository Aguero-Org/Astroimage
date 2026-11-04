from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import asdict, dataclass
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.deps import fits_service_from_resources
from astroimage.fits.reader import FitsReader
from astroimage.fits.service import FitsService
from astroimage.render.model import ImagePreview
from astroimage.render.png import thumbnail_png
from astroimage.render.repository import PreviewRepository
from astroimage.render.service import RenderService, render_png_bytes
from astroimage.render.spec import RenderConfig
from astroimage.shared.background import BackgroundTasks
from astroimage.shared.errors import BadRequestError
from astroimage.shared.logging import preview_log as _log
from astroimage.shared.object_storage import ObjectStorage

PRESET_ID = "equilibrio"
PREVIEW_EDGES = (256, 512, 1024)
_UNAVAILABLE_SIZE = "Preview size is not available"
EQUILIBRIO = RenderConfig(
    stretch="linear",
    limits="percentiles",
    colormap="grey",
    pmin=1.0,
    pmax=99.0,
    gamma=0.5,
)


class _PreviewStore(Protocol):
    async def find(
        self,
        record_id: UUID,
        preset_id: str,
        edge_px: int,
    ) -> ImagePreview | None: ...

    async def save(self, preview: ImagePreview) -> ImagePreview: ...


def preview_config_hash(preset_id: str, edge_px: int, config: RenderConfig) -> str:
    document = {
        "preset_id": preset_id,
        "edge_px": edge_px,
        "config": asdict(config),
    }
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def preview_object_key(record_id: UUID, preset_id: str, edge_px: int) -> str:
    return f"previews/{record_id}/{preset_id}/{edge_px}.png"


def preview_etag(edge_px: int) -> str:
    return f'"{preview_config_hash(PRESET_ID, edge_px, EQUILIBRIO)}"'


@dataclass(frozen=True)
class PreviewImage:
    content: bytes
    etag: str | None


def _repository_for(session: Any) -> PreviewRepository:
    return PreviewRepository(session)


class PreviewService:
    def __init__(
        self,
        tasks: BackgroundTasks,
        session_factory: Callable[[], AbstractAsyncContextManager[Any]],
        storage: ObjectStorage,
        *,
        session: Any | None = None,
        reader: FitsReader | None = None,
        fits: FitsService | None = None,
        fits_factory: Callable[[Any], Any] | None = None,
        repository_factory: Callable[[Any], _PreviewStore] | None = None,
    ) -> None:
        self._tasks = tasks
        self._session_factory = session_factory
        self._storage = storage
        self._session = session
        self._reader = reader
        self._fits = fits
        self._fits_factory = fits_factory or self._default_fits_factory
        self._repository_factory = repository_factory or _repository_for

    def _default_fits_factory(self, session: Any) -> FitsService:
        return fits_service_from_resources(session, self._storage)

    def for_request(
        self,
        session: AsyncSession,
        reader: FitsReader,
        fits: FitsService,
    ) -> PreviewService:
        return PreviewService(
            self._tasks,
            self._session_factory,
            self._storage,
            session=session,
            reader=reader,
            fits=fits,
            fits_factory=self._fits_factory,
            repository_factory=self._repository_factory,
        )

    def schedule(self, record_id: UUID) -> None:
        self._tasks.start(f"preview:{record_id}", lambda: self._run(record_id))

    async def png(self, record_id: UUID, edge_px: int) -> PreviewImage:
        if edge_px not in PREVIEW_EDGES:
            raise BadRequestError(_UNAVAILABLE_SIZE)
        if self._session is None or self._reader is None or self._fits is None:
            raise TypeError("Preview read is not configured")
        stored = await self._current_bytes(self._session, record_id, edge_px)
        if stored is not None:
            return PreviewImage(content=stored, etag=preview_etag(edge_px))
        full = await RenderService(self._reader, self._fits).png_for_record(
            record_id,
            config=EQUILIBRIO,
        )
        png = await asyncio.to_thread(thumbnail_png, full, edge_px)
        return PreviewImage(content=png, etag=None)

    async def render_stored(self, record_id: UUID) -> None:
        if await self._all_current(record_id):
            return
        png = await self._full_png(record_id)
        thumbnails = {
            edge: await asyncio.to_thread(thumbnail_png, png, edge) for edge in PREVIEW_EDGES
        }
        async with self._session_factory() as session:
            repository = self._repository_factory(session)
            for edge in PREVIEW_EDGES:
                await self._upsert(repository, record_id, edge, thumbnails[edge])
            await session.commit()

    async def backfill_missing(self) -> None:
        try:
            async with self._session_factory() as session:
                record_ids = await self._fits_factory(session).list_record_ids()
        except Exception:
            _log.exception("preview_backfill_failed")
            return
        for record_id in record_ids:
            await self._run(record_id)

    async def _run(self, record_id: UUID) -> None:
        try:
            await self.render_stored(record_id)
        except Exception:
            _log.exception("preview_render_failed", record_id=str(record_id))

    async def _all_current(self, record_id: UUID) -> bool:
        async with self._session_factory() as session:
            for edge in PREVIEW_EDGES:
                if await self._current_bytes(session, record_id, edge) is None:
                    return False
        return True

    async def _current_bytes(
        self,
        session: Any,
        record_id: UUID,
        edge_px: int,
    ) -> bytes | None:
        preview = await self._repository_factory(session).find(record_id, PRESET_ID, edge_px)
        if preview is None or preview.config_hash != preview_config_hash(
            PRESET_ID,
            edge_px,
            EQUILIBRIO,
        ):
            return None
        try:
            return await self._storage.get_bytes(preview.object_key)
        except LookupError:
            return None

    async def _object_present(self, object_key: str) -> bool:
        try:
            await self._storage.get_bytes(object_key)
        except LookupError:
            return False
        return True

    async def _full_png(self, record_id: UUID) -> bytes:
        async with self._session_factory() as session:
            source = self._fits_factory(session)
            record = await source.get_record(record_id)
            payload = await source.get_payload(record)
        return await asyncio.to_thread(render_png_bytes, FitsReader(), payload, EQUILIBRIO)

    async def _upsert(
        self,
        repository: _PreviewStore,
        record_id: UUID,
        edge_px: int,
        png: bytes,
    ) -> None:
        config_hash = preview_config_hash(PRESET_ID, edge_px, EQUILIBRIO)
        object_key = preview_object_key(record_id, PRESET_ID, edge_px)
        existing = await repository.find(record_id, PRESET_ID, edge_px)
        if (
            existing is not None
            and existing.config_hash == config_hash
            and await self._object_present(existing.object_key)
        ):
            return
        await self._storage.put_bytes(object_key, png, content_type="image/png")
        if existing is None:
            await repository.save(
                ImagePreview(
                    record_id=record_id,
                    preset_id=PRESET_ID,
                    edge_px=edge_px,
                    config_hash=config_hash,
                    object_key=object_key,
                )
            )
            return
        existing.config_hash = config_hash
        existing.object_key = object_key
