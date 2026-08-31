from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from uuid import UUID

from astroimage.fits.model import FitsRecord
from astroimage.fits.reader import FitsImageData, FitsMetadata, FitsReader
from astroimage.fits.repository import FitsRepository
from astroimage.fits.schema import FitsMetadataSchema
from astroimage.fits.storage import FitsStorage


class FitsService:
    def __init__(
        self,
        reader: FitsReader,
        repository: FitsRepository,
        storage: FitsStorage,
    ) -> None:
        self._reader = reader
        self._repository = repository
        self._storage = storage

    def metadata_from_path(
        self,
        path: Path | str,
        *,
        hdu_index: int | None = None,
    ) -> FitsMetadata:
        return self._reader.read_metadata_from_path(path, hdu_index=hdu_index)

    def metadata_from_bytes(
        self,
        payload: bytes,
        *,
        source_name: str,
        hdu_index: int | None = None,
    ) -> FitsMetadata:
        if not payload:
            raise ValueError("Empty FITS payload")
        return self._reader.read_metadata_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )

    def image_data_from_path(
        self,
        path: Path | str,
        *,
        hdu_index: int | None = None,
    ) -> FitsImageData:
        return self._reader.read_image_data_from_path(path, hdu_index=hdu_index)

    def image_data_from_bytes(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
    ) -> FitsImageData:
        return self._reader.read_image_data_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )

    def to_schema(self, metadata: FitsMetadata) -> FitsMetadataSchema:
        return FitsMetadataSchema.model_validate(metadata.model_dump())

    async def store_bytes(
        self,
        payload: bytes,
        *,
        source_name: str,
        hdu_index: int | None = None,
    ) -> FitsRecord:
        metadata = self.metadata_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )
        object_key = await self._storage.put(payload, source_name=source_name)
        record = FitsRecord(
            object_key=object_key,
            original_filename=source_name,
            size_bytes=len(payload),
            metadata_payload=metadata.model_dump(mode="json"),
        )
        try:
            return await self._repository.create(record)
        except Exception:
            await self._storage.remove(object_key)
            raise

    async def get_record(self, record_id: UUID) -> FitsRecord:
        return await self._repository.get(record_id)

    async def list_records(self, *, offset: int = 0, limit: int = 100) -> Sequence[FitsRecord]:
        return await self._repository.list(offset=offset, limit=limit)

    async def get_payload(self, record: FitsRecord) -> bytes:
        return await self._storage.get(record.object_key)

    async def replace_bytes(
        self,
        record_id: UUID,
        payload: bytes,
        *,
        source_name: str,
        hdu_index: int | None = None,
    ) -> FitsRecord:
        record = await self.get_record(record_id)
        metadata = self.metadata_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )
        await self._storage.put_at(record.object_key, payload)
        record.original_filename = source_name
        record.size_bytes = len(payload)
        record.metadata_payload = metadata.model_dump(mode="json")
        return await self._repository.update(record)

    async def delete_record(self, record_id: UUID) -> None:
        record = await self.get_record(record_id)
        await self._repository.delete(record)
        await self._storage.remove(record.object_key)
