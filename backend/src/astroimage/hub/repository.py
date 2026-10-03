from __future__ import annotations

from typing import cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.hub.model import (
    ACTIVE_TRANSFER_STATUSES,
    ImageTransfer,
    TransferStatus,
)


class TransferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, transfer: ImageTransfer) -> ImageTransfer:
        self._session.add(transfer)
        await self._session.flush()
        await self._session.refresh(transfer)
        return transfer

    async def get(self, transfer_id: UUID) -> ImageTransfer:
        transfer = await self._session.get(ImageTransfer, transfer_id)
        if transfer is None:
            raise LookupError(f"transfer not found: {transfer_id}")
        return transfer

    async def commit(self) -> None:
        await self._session.commit()

    async def save(self, transfer: ImageTransfer) -> ImageTransfer:
        await self._session.flush()
        await self._session.refresh(transfer)
        return transfer

    async def find_latest_by_data_uri(self, data_uri: str) -> ImageTransfer | None:
        statement = (
            select(ImageTransfer)
            .where(ImageTransfer.data_uri == data_uri)
            .order_by(ImageTransfer.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def mark_running_as_interrupted(self) -> int:
        statement = (
            update(ImageTransfer)
            .where(ImageTransfer.status.in_([status.value for status in ACTIVE_TRANSFER_STATUSES]))
            .values(status=TransferStatus.INTERRUPTED.value, error="process restarted")
        )
        result = await self._session.execute(statement)
        await self._session.flush()
        cursor = cast(CursorResult[object], result)
        return int(cursor.rowcount or 0)
