from __future__ import annotations

import time
from uuid import UUID

import structlog
from opentelemetry import trace

from astroimage.fits.schema import FitsMetadataSchema
from astroimage.fits.service import FitsService
from astroimage.hub.importer import HubbleImporter
from astroimage.hub.schema import (
    FetchImageResponseSchema,
    ListRecordsResponseSchema,
)

_log = structlog.get_logger("astroimage.hub.service")
_tracer = trace.get_tracer("astroimage.hub.service")


class HubbleImageService:
    def __init__(self, importer: HubbleImporter, fits: FitsService) -> None:
        self._importer = importer
        self._fits = fits

    async def fetch(self, target_name: str) -> FetchImageResponseSchema:
        with _tracer.start_as_current_span("hub_fetch") as span:
            image = await self._importer.fetch_image(target_name)
            span.set_attribute("observation_id", image.observation_id)
            span.set_attribute("instrument", image.instrument or "unknown")

            _log.info(
                "import_complete",
                target_name=target_name,
                observation_id=image.observation_id,
                payload_bytes=len(image.payload),
            )

            with _tracer.start_as_current_span("fits_store"):
                store_start = time.perf_counter()
                record = await self._fits.store_bytes(
                    image.payload,
                    source_name=target_name,
                    analyze=False,
                )
                store_ms = round((time.perf_counter() - store_start) * 1000, 2)
                _log.info(
                    "store_complete",
                    target_name=target_name,
                    record_id=str(record.id),
                    store_ms=store_ms,
                )

            span.set_attribute("record_id", str(record.id))
            return FetchImageResponseSchema(record_id=record.id)

    async def list_records(self, *, offset: int = 0, limit: int = 100) -> ListRecordsResponseSchema:
        summaries = await self._fits.list_record_summaries(offset=offset, limit=limit)
        _log.info(
            "list_records_complete",
            count=len(summaries),
        )
        return ListRecordsResponseSchema(records=list(summaries))

    async def search_records(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> ListRecordsResponseSchema:
        summaries = await self._fits.search_record_summaries(
            name,
            offset=offset,
            limit=limit,
        )
        _log.info(
            "search_records_complete",
            name=name,
            count=len(summaries),
        )
        return ListRecordsResponseSchema(records=list(summaries))

    async def get_record_info(self, record_id: UUID) -> FitsMetadataSchema:
        return await self._fits.get_record_metadata(record_id)
