from __future__ import annotations

import hashlib
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit
from uuid import UUID, uuid4

import httpx
import structlog
from opentelemetry import trace

from astroimage.fits.model import FitsRecord
from astroimage.fits.reader import FitsImageData, FitsMetadata, FitsReader
from astroimage.fits.repository import FitsRepository
from astroimage.fits.schema import FitsMetadataSchema, FitsRecordSummarySchema
from astroimage.fits.storage import FitsStorage
from astroimage.shared.errors import BadRequestError, ConflictError

_log = structlog.get_logger("astroimage.fits.service")


def _keeping_mast(metadata: dict[str, Any], previous: object) -> dict[str, Any]:
    if not isinstance(previous, dict) or "mast" not in previous:
        return metadata
    return {**metadata, "mast": previous["mast"]}


def _text_or_none(value: object) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value)
    if isinstance(value, str) and value.strip() != "":
        return value.strip()
    return None


def _optional_text(value: str | None, *, limit: int, message: str) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if text == "":
        return None
    if len(text) > limit:
        raise BadRequestError(message)
    return text


def _local_fields(
    record: FitsRecord,
) -> tuple[str, str | None, str | None, str | None, str | None, None]:
    payload = record.metadata_payload if isinstance(record.metadata_payload, dict) else {}
    raw_instrument = payload.get("instrument")
    instrument = raw_instrument if isinstance(raw_instrument, dict) else {}
    raw_header = payload.get("header")
    header = raw_header if isinstance(raw_header, dict) else {}
    proposal = _text_or_none(header.get("PROPOSID")) or _text_or_none(header.get("PROPNUM"))
    return (
        _text_or_none(payload.get("display_name")) or record.original_filename,
        _text_or_none(instrument.get("instrument")),
        proposal,
        _text_or_none(instrument.get("filter_name")),
        _text_or_none(instrument.get("date_obs")),
        None,
    )


def _summary_fields(
    record: FitsRecord,
) -> tuple[str, str | None, str | None, str | None, str | None, str | None]:
    payload = record.metadata_payload
    raw_mast = payload.get("mast") if isinstance(payload, dict) else None
    if isinstance(raw_mast, dict):
        return _mast_fields(record)
    return _local_fields(record)


def _filename_from_url(url: str) -> str:
    path = unquote(urlsplit(url).path)
    name = Path(path).name.strip()
    if name == "" or name in {".", ".."}:
        return "upload.fits"
    return name


_MAST_DOWNLOAD = "https://mast.stsci.edu/api/v0.1/Download/file"


def _normalize_import_url(url: str) -> str:
    stripped = url.strip()
    parts = urlsplit(stripped)
    scheme = parts.scheme.casefold()
    if scheme in {"http", "https"} and parts.netloc != "":
        return stripped
    if scheme != "mast":
        raise BadRequestError("The FITS URL must be an absolute http, https, or MAST address")
    body = parts.path.lstrip("/")
    if parts.netloc != "":
        body = parts.netloc if body == "" else f"{parts.netloc}/{body}"
    if body == "":
        raise BadRequestError("The FITS URL must be an absolute http, https, or MAST address")
    return f"mast:{body}"


def _fetch_url(normalized: str) -> str:
    if normalized.casefold().startswith("mast:"):
        return f"{_MAST_DOWNLOAD}?uri={quote(normalized, safe=':/')}"
    return normalized


async def _download_fits(url: str, max_bytes: int) -> bytes:
    try:
        async with (
            httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client,
            client.stream("GET", url) as response,
        ):
            if response.status_code >= 400:
                raise BadRequestError("Could not download the FITS file")
            declared = response.headers.get("content-length")
            if declared is not None and declared.isdigit() and int(declared) > max_bytes:
                raise BadRequestError("FITS file exceeds the size limit")
            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > max_bytes:
                    raise BadRequestError("FITS file exceeds the size limit")
                chunks.append(chunk)
    except httpx.HTTPError as exc:
        raise BadRequestError("Could not download the FITS file") from exc
    return b"".join(chunks)


def _mast_fields(
    record: FitsRecord,
) -> tuple[str, str | None, str, str | None, str | None, str]:
    payload = record.metadata_payload
    raw_mast = payload.get("mast") if isinstance(payload, dict) else None
    mast = raw_mast if isinstance(raw_mast, dict) else None
    if mast is None:
        raise ValueError(f"FITS record {record.id} is missing MAST provenance")
    data_uri = mast.get("data_uri")
    proposal_id = mast.get("proposal_id")
    display_name = mast.get("display_name")
    if not isinstance(data_uri, str) or data_uri == "":
        raise ValueError(f"FITS record {record.id} is missing MAST data URI")
    if not isinstance(proposal_id, str) or proposal_id == "":
        raise ValueError(f"FITS record {record.id} is missing MAST proposal id")
    if not isinstance(display_name, str) or display_name == "":
        raise ValueError(f"FITS record {record.id} is missing display name")
    return (
        display_name,
        _text_or_none(mast.get("instrument")),
        proposal_id,
        _text_or_none(mast.get("filters")),
        _text_or_none(mast.get("observed_at")),
        data_uri,
    )


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

    async def find_record_id_by_mast_data_uri(self, data_uri: str) -> UUID | None:
        record = await self._repository.find_by_mast_data_uri(data_uri)
        if record is None:
            return None
        return record.id

    async def store_bytes(
        self,
        payload: bytes,
        *,
        source_name: str,
        hdu_index: int | None = None,
        analyze: bool = True,
        slug: str | None = None,
        original_filename: str | None = None,
        provenance: dict[str, Any] | None = None,
        content_hash: str | None = None,
        source_url: str | None = None,
        description: str | None = None,
        display_name: str | None = None,
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
            if provenance is not None:
                metadata_payload = {**metadata_payload, "mast": provenance}
            text = _optional_text(
                description,
                limit=500,
                message="The description is too long",
            )
            title = _optional_text(
                display_name,
                limit=200,
                message="The title is too long",
            )
            if text is not None:
                metadata_payload = {**metadata_payload, "description": text}
            if title is not None:
                metadata_payload = {**metadata_payload, "display_name": title}
            record = FitsRecord(
                id=record_id,
                object_key=object_key,
                slug=slug or source_name,
                original_filename=original_filename or source_name,
                size_bytes=len(payload),
                content_hash=content_hash,
                source_url=source_url,
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

    async def import_bytes(
        self,
        payload: bytes,
        *,
        source_name: str,
        max_bytes: int,
        source_url: str | None = None,
        description: str | None = None,
        display_name: str | None = None,
    ) -> FitsRecord:
        if len(payload) > max_bytes:
            raise BadRequestError("FITS file exceeds the size limit")
        content_hash = hashlib.sha256(payload).hexdigest()
        existing = await self._repository.find_by_content_hash(content_hash)
        if existing is not None:
            raise ConflictError("A FITS file with the same content is already stored")
        return await self.store_bytes(
            payload,
            source_name=source_name,
            content_hash=content_hash,
            source_url=source_url,
            description=description,
            display_name=display_name,
        )

    async def import_from_url(
        self,
        url: str,
        *,
        max_bytes: int,
        description: str | None = None,
        display_name: str | None = None,
    ) -> FitsRecord:
        normalized = _normalize_import_url(url)
        existing = await self._repository.find_by_source_url(normalized)
        if existing is not None:
            raise ConflictError("This URL is already imported")
        payload = await _download_fits(_fetch_url(normalized), max_bytes)
        return await self.import_bytes(
            payload,
            source_name=_filename_from_url(normalized),
            max_bytes=max_bytes,
            source_url=normalized,
            description=description,
            display_name=display_name,
        )

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
            record.metadata_payload = _keeping_mast(
                metadata.model_dump(mode="json"),
                record.metadata_payload,
            )
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
        payload = record.metadata_payload
        document = payload if isinstance(payload, dict) else {}
        mast = document.get("mast")
        public = {
            key: value
            for key, value in document.items()
            if key not in {"mast", "description", "display_name"}
        }
        if isinstance(mast, dict):
            catalog_name = mast.get("display_name")
            if isinstance(catalog_name, str) and catalog_name != "":
                public["display_name"] = catalog_name
        return FitsMetadataSchema.model_validate(public)

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
        display_name, instrument, proposal_id, filters, observed_at, data_uri = _summary_fields(
            record
        )
        return FitsRecordSummarySchema(
            record_id=record.id,
            slug=record.slug,
            name=record.original_filename,
            display_name=display_name,
            instrument=instrument,
            proposal_id=proposal_id,
            filters=filters,
            observed_at=observed_at,
            created_at=record.created_at,
            size_bytes=record.size_bytes,
            data_uri=data_uri,
            description=_text_or_none(
                record.metadata_payload.get("description")
                if isinstance(record.metadata_payload, dict)
                else None
            ),
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
                    slug=filename,
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
