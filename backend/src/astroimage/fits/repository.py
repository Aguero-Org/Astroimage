from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.model import FitsRecord


class FitsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: FitsRecord) -> FitsRecord:
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def get(self, record_id: UUID) -> FitsRecord:
        record = await self._session.get(FitsRecord, record_id)
        if record is None:
            raise LookupError(f"FITS record not found: {record_id}")
        return record

    async def get_by_object_key(self, object_key: str) -> FitsRecord:
        statement = select(FitsRecord).where(FitsRecord.object_key == object_key)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(f"FITS object not found: {object_key}")
        return record

    async def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[FitsRecord]:
        statement = (
            select(FitsRecord).order_by(FitsRecord.created_at.desc()).offset(offset).limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def list_by_name(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[FitsRecord]:
        statement = (
            select(FitsRecord)
            .where(FitsRecord.original_filename.ilike(f"%{name}%"))
            .order_by(FitsRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def update(self, record: FitsRecord) -> FitsRecord:
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def delete(self, record: FitsRecord) -> None:
        await self._session.delete(record)
        await self._session.flush()
