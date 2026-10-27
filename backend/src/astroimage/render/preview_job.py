from __future__ import annotations

import asyncio
import hashlib
import json
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from astroimage.fits.deps import fits_service_from_resources
from astroimage.render.model import ImagePreview
from astroimage.render.png import thumbnail_png
from astroimage.render.repository import PreviewRepository
from astroimage.render.schema import RenderConfigSchema
from astroimage.render.service import RenderService
from astroimage.shared.background import BackgroundTasks
from astroimage.shared.errors import BadRequestError
from astroimage.shared.object_storage import ObjectStorage

_log = structlog.get_logger("astroimage.render.preview")

BASE_PRESET_ID = "equilibrio"
PREVIEW_EDGES = (256, 512, 1024)
_BASE_CONFIG = RenderConfigSchema()


def preview_config_hash(preset_id: str, edge_px: int) -> str:
    document = {
        "preset_id": preset_id,
        "edge_px": edge_px,
        "config": _BASE_CONFIG.model_dump(mode="json"),
    }
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def preview_object_key(record_id: UUID, preset_id: str, edge_px: int) -> str:
    return f"previews/{record_id}/{preset_id}/{edge_px}.png"


class PreviewRenderer:
    def __init__(
        self,
        tasks: BackgroundTasks,
        session_factory: async_sessionmaker[AsyncSession],
        storage: ObjectStorage,
    ) -> None:
        self._tasks = tasks
        self._session_factory = session_factory
        self._storage = storage

    def schedule(self, record_id: UUID) -> None:
        self._tasks.start(f"preview:{record_id}", lambda: self._render(record_id))

    async def stored_png(
        self, session: AsyncSession, record_id: UUID, edge_px: int
    ) -> bytes | None:
        if edge_px not in PREVIEW_EDGES:
            raise BadRequestError("Preview size is not available")
        preview = await PreviewRepository(session).find(record_id, BASE_PRESET_ID, edge_px)
        if preview is None:
            return None
        return await self._storage.get_bytes(preview.object_key)

    async def render_fallback(
        self,
        session: AsyncSession,
        record_id: UUID,
        edge_px: int,
    ) -> bytes:
        if edge_px not in PREVIEW_EDGES:
            raise BadRequestError("Preview size is not available")
        fits = fits_service_from_resources(session, self._storage)
        png = await RenderService(fits=fits).render_png_from_record(record_id)
        return await asyncio.to_thread(thumbnail_png, png, edge_px)

    async def _render(self, record_id: UUID) -> None:
        try:
            async with self._session_factory() as session:
                fits = fits_service_from_resources(session, self._storage)
                record = await fits.get_record(record_id)
                payload = await fits.get_payload(record)
                full = await asyncio.to_thread(RenderService().render_png_from_bytes, payload)
                repository = PreviewRepository(session)
                for edge in PREVIEW_EDGES:
                    config_hash = preview_config_hash(BASE_PRESET_ID, edge)
                    existing = await repository.find(record_id, BASE_PRESET_ID, edge)
                    if existing is not None and existing.config_hash == config_hash:
                        continue
                    png = await asyncio.to_thread(thumbnail_png, full, edge)
                    object_key = preview_object_key(record_id, BASE_PRESET_ID, edge)
                    await self._storage.put_bytes(
                        object_key,
                        png,
                        content_type="image/png",
                    )
                    if existing is None:
                        await repository.save(
                            ImagePreview(
                                record_id=record_id,
                                preset_id=BASE_PRESET_ID,
                                edge_px=edge,
                                config_hash=config_hash,
                                object_key=object_key,
                            )
                        )
                    else:
                        existing.config_hash = config_hash
                        existing.object_key = object_key
                await session.commit()
        except Exception:  # noqa: BLE001
            _log.exception("preview_render_failed", record_id=str(record_id))
