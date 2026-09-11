from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

import structlog
from opentelemetry import trace

from astroimage.fits.model import FitsRecord
from astroimage.fits.reader import FitsImageData, FitsMetadata, FitsReader
from astroimage.fits.repository import FitsRepository
from astroimage.fits.schema import FitsMetadataSchema, FitsRecordSummarySchema
from astroimage.fits.storage import FitsStorage

_log = structlog.get_logger("astroimage.fits.service")
_tracer = trace.get_tracer("astroimage.fits.service")


@dataclass(frozen=True)
class ReconcileReport:
    created: list[str]
    updated: list[str]
    skipped: list[str]
    failed: list[str]


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
        analyze: bool = True,
    ) -> FitsRecord:
        with _tracer.start_as_current_span("fits_store_bytes") as span:
            span.set_attribute("source_name", source_name)
            span.set_attribute("payload_bytes", len(payload))
            span.set_attribute("analyze", analyze)
            if analyze:
                metadata_payload = self.metadata_from_bytes(
                    payload,
                    source_name=source_name,
                    hdu_index=hdu_index,
                ).model_dump(mode="json")
            else:
                metadata_payload = {
                    "source_name": source_name,
                    "hdus": {"selected": 0},
                }
            record_id = uuid4()
            object_key = self._storage.object_key_for(record_id, source_name)
            record = FitsRecord(
                id=record_id,
                object_key=object_key,
                original_filename=source_name,
                size_bytes=len(payload),
                metadata_payload=metadata_payload,
            )
            await self._repository.create(record)
            upload_start = time.perf_counter()
            try:
                await self._storage.put_at(object_key, payload)
            except Exception:
                await self._repository.delete(record)
                raise
            upload_ms = round((time.perf_counter() - upload_start) * 1000, 2)
            _log.info(
                "fits_store_complete",
                record_id=str(record_id),
                source_name=source_name,
                size_bytes=len(payload),
                upload_ms=upload_ms,
            )
            span.set_attribute("record_id", str(record_id))
            return record

    async def update_record_metadata(
        self,
        record: FitsRecord,
        payload: bytes,
        *,
        hdu_index: int | None = None,
    ) -> FitsRecord:
        with _tracer.start_as_current_span("fits_update_metadata") as span:
            span.set_attribute("record_id", str(record.id))
            analyze_start = time.perf_counter()
            metadata = self.metadata_from_bytes(
                payload,
                source_name=record.original_filename,
                hdu_index=hdu_index,
            )
            analyze_ms = round((time.perf_counter() - analyze_start) * 1000, 2)
            record.metadata_payload = metadata.model_dump(mode="json")
            updated = await self._repository.update(record)
            _log.info(
                "metadata_updated",
                record_id=str(record.id),
                analyze_ms=analyze_ms,
            )
            return updated

    async def get_record(self, record_id: UUID) -> FitsRecord:
        record = await self._repository.get(record_id)
        _log.debug("record_loaded", record_id=str(record_id))
        return record

    async def get_record_metadata(self, record_id: UUID) -> FitsMetadataSchema:
        record = await self.get_record(record_id)
        return FitsMetadataSchema.model_validate(record.metadata_payload)

    async def list_records(self, *, offset: int = 0, limit: int = 100) -> Sequence[FitsRecord]:
        return await self._repository.list(offset=offset, limit=limit)

    async def list_records_by_name(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[FitsRecord]:
        return await self._repository.list_by_name(
            name,
            offset=offset,
            limit=limit,
        )

    async def list_record_summaries(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[FitsRecordSummarySchema]:
        records = await self._repository.list(offset=offset, limit=limit)
        return [self._to_summary(record) for record in records]

    async def search_record_summaries(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[FitsRecordSummarySchema]:
        records = await self._repository.list_by_name(
            name,
            offset=offset,
            limit=limit,
        )
        return [self._to_summary(record) for record in records]

    @staticmethod
    def _to_summary(record: FitsRecord) -> FitsRecordSummarySchema:
        return FitsRecordSummarySchema(
            record_id=record.id,
            name=record.original_filename,
        )

    async def get_payload(self, record: FitsRecord) -> bytes:
        payload = await self._storage.get(record.object_key)
        _log.debug(
            "payload_loaded",
            record_id=str(record.id),
            payload_bytes=len(payload),
        )
        return payload

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

    async def reconcile_records(self) -> ReconcileReport:
        object_keys = await self._storage.list_fits_keys()
        created: list[str] = []
        updated: list[str] = []
        skipped: list[str] = []
        failed: list[str] = []
        for object_key in object_keys:
            try:
                record_id = UUID(Path(object_key).stem)
            except ValueError:
                failed.append(object_key)
                continue
            try:
                payload = await self._storage.get(object_key)
                metadata = self.metadata_from_bytes(
                    payload,
                    source_name=Path(object_key).name,
                )
                real_name = self._reader.source_filename_from_bytes(payload)
                filename = str(real_name or Path(object_key).name)
                metadata = metadata.model_copy(update={"source_name": filename})
            except (OSError, ValueError):
                failed.append(object_key)
                continue
            try:
                existing = await self._repository.get(record_id)
            except LookupError:
                record = FitsRecord(
                    id=record_id,
                    object_key=object_key,
                    original_filename=filename,
                    size_bytes=len(payload),
                    metadata_payload=metadata.model_dump(mode="json"),
                )
                await self._repository.create(record)
                created.append(object_key)
                continue
            fallback_name = f"{record_id}.fits"
            if existing.original_filename == fallback_name and filename != fallback_name:
                existing.original_filename = filename
                await self._repository.update(existing)
                updated.append(object_key)
            else:
                skipped.append(object_key)
        _log.info(
            "reconcile_complete",
            created=len(created),
            updated=len(updated),
            skipped=len(skipped),
            failed=len(failed),
        )
        return ReconcileReport(
            created=created,
            updated=updated,
            skipped=skipped,
            failed=failed,
        )
