from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.render.model import ImagePreview


class PreviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find(self, record_id: UUID, preset_id: str, edge_px: int) -> ImagePreview | None:
        statement = select(ImagePreview).where(
            ImagePreview.record_id == record_id,
            ImagePreview.preset_id == preset_id,
            ImagePreview.edge_px == edge_px,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def save(self, preview: ImagePreview) -> ImagePreview:
        self._session.add(preview)
        await self._session.flush()
        return preview
