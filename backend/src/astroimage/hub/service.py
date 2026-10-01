from __future__ import annotations

import time
from collections.abc import Callable
from uuid import UUID

import httpx
import structlog
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from astroimage.fits.schema import FitsMetadataSchema
from astroimage.fits.service import FitsService
from astroimage.hub.candidate_token import read_candidate_token, sign_candidate_token
from astroimage.hub.importer import HubbleImporter, HubbleProduct
from astroimage.hub.model import (
    ACTIVE_TRANSFER_STATUSES,
    RESUMABLE_TRANSFER_STATUSES,
    ImageTransfer,
    TransferStatus,
)
from astroimage.hub.progress import progress_ratio
from astroimage.hub.record_page import filter_summaries, page_summaries
from astroimage.hub.repository import TransferRepository
from astroimage.hub.runner import TransferRunner
from astroimage.hub.schema import (
    CandidatePageSchema,
    CandidateSchema,
    CandidateSortField,
    CandidateSortOrder,
    FetchImageResponseSchema,
    ListRecordsResponseSchema,
    RecordSortField,
    TransferStatusSchema,
)
from astroimage.hub.sorting import sort_products
from astroimage.shared.background import BackgroundTasks
from astroimage.shared.object_storage import ObjectStorage

_log = structlog.get_logger("astroimage.hub.service")
CATALOG_READ_LIMIT = 500
_tracer = trace.get_tracer("astroimage.hub.service")


class HubbleImageService:
    def __init__(
        self,
        importer: HubbleImporter,
        fits: FitsService,
        *,
        transfers: TransferRepository | None = None,
        tasks: BackgroundTasks | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        storage: ObjectStorage | None = None,
        token_secret: str = "",
        fits_factory: Callable[[AsyncSession], FitsService] | None = None,
        http_client_factory: Callable[[], httpx.AsyncClient] | None = None,
    ) -> None:
        self._importer = importer
        self._fits = fits
        self._transfers = transfers
        self._tasks = tasks
        self._session_factory = session_factory
        self._storage = storage
        self._token_secret = token_secret
        self._fits_factory = fits_factory
        self._http_client_factory = http_client_factory or (
            lambda: httpx.AsyncClient(timeout=300.0)
        )

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
            return FetchImageResponseSchema(
                record_id=record.id,
                slug=record.slug,
            )

    async def list_records(
        self,
        *,
        page: int = 1,
        limit: int = 8,
        sort: RecordSortField = "created_at",
        order: CandidateSortOrder = "desc",
    ) -> ListRecordsResponseSchema:
        summaries = await self._fits.list_record_summaries(offset=0, limit=CATALOG_READ_LIMIT)
        _log.info("list_records_complete", count=len(summaries))
        return page_summaries(
            list(summaries),
            page=page,
            limit=limit,
            sort=sort,
            order=order,
        )

    async def search_records(
        self,
        name: str,
        *,
        page: int = 1,
        limit: int = 8,
        sort: RecordSortField = "created_at",
        order: CandidateSortOrder = "desc",
    ) -> ListRecordsResponseSchema:
        summaries = await self._fits.list_record_summaries(offset=0, limit=CATALOG_READ_LIMIT)
        matched = filter_summaries(list(summaries), name)
        _log.info("search_records_complete", name=name, count=len(matched))
        return page_summaries(
            matched,
            page=page,
            limit=limit,
            sort=sort,
            order=order,
        )

    async def delete_record(self, record_id: UUID) -> None:
        await self._fits.delete_record(record_id)

    async def get_record_info(self, record_id: UUID) -> FitsMetadataSchema:
        return await self._fits.get_record_metadata(record_id)

    async def search_candidates(
        self,
        target_name: str,
        *,
        page: int,
        limit: int,
        min_size_mb: float | None,
        sort: CandidateSortField,
        order: CandidateSortOrder,
    ) -> CandidatePageSchema:
        min_size_bytes = None if min_size_mb is None else int(min_size_mb * 1024 * 1024)
        products = await self._importer.search_candidates(
            target_name,
            min_size_bytes=min_size_bytes,
        )
        ordered = sort_products(products, sort=sort, order=order)
        start = (page - 1) * limit
        page_items = ordered[start : start + limit]
        items = [self._candidate_schema(target_name, product) for product in page_items]
        return CandidatePageSchema(
            items=items,
            page=page,
            limit=limit,
            has_more=len(ordered) > start + limit,
            sort=sort,
            order=order,
        )

    async def select_candidate(
        self, candidate_token: str, display_name: str
    ) -> TransferStatusSchema:
        payload = read_candidate_token(candidate_token, self._token_secret)
        data_uri = str(payload["data_uri"])
        repository = self._require_transfers()
        existing = await repository.find_latest_by_data_uri(data_uri)
        if existing is not None and existing.status == TransferStatus.COMPLETED.value:
            return self._transfer_schema(existing)
        if existing is not None and existing.status in {
            status.value for status in ACTIVE_TRANSFER_STATUSES
        }:
            return self._transfer_schema(existing)
        if existing is not None and existing.status in {
            status.value for status in RESUMABLE_TRANSFER_STATUSES
        }:
            return await self.resume(existing.id)
        stored = await self._fits.find_record_id_by_mast_data_uri(data_uri)
        transfer = ImageTransfer(
            status=TransferStatus.COMPLETED.value if stored else TransferStatus.QUEUED.value,
            source="mast",
            destination="astroimage",
            target_name=str(payload.get("target_name") or ""),
            display_name=display_name,
            data_uri=data_uri,
            product_filename=str(payload.get("product_filename") or "product.fits"),
            observation_id=str(payload.get("observation_id") or ""),
            proposal_id=str(payload.get("proposal_id") or ""),
            instrument=payload.get("instrument"),
            filters=payload.get("filters"),
            observed_at=payload.get("observed_at"),
            ra_deg=float(payload.get("ra_deg") or 0),
            dec_deg=float(payload.get("dec_deg") or 0),
            bytes_transferred=0,
            total_bytes=payload.get("size_bytes"),
            record_id=stored,
            samples=[],
        )
        created = await repository.create(transfer)
        if stored is None:
            await repository.commit()
            self._start(created.id)
        return self._transfer_schema(created)

    async def get_transfer(self, transfer_id: UUID) -> TransferStatusSchema:
        transfer = await self._require_transfers().get(transfer_id)
        return self._transfer_schema(transfer)

    async def cancel(self, transfer_id: UUID) -> TransferStatusSchema:
        repository = self._require_transfers()
        transfer = await repository.get(transfer_id)
        if transfer.status in {
            TransferStatus.COMPLETED.value,
            TransferStatus.FAILED.value,
            TransferStatus.CANCELLED.value,
        }:
            return self._transfer_schema(transfer)
        transfer.status = TransferStatus.CANCELLED.value
        await repository.save(transfer)
        if self._tasks is not None:
            self._tasks.cancel(str(transfer_id))
        return self._transfer_schema(transfer)

    async def resume(self, transfer_id: UUID) -> TransferStatusSchema:
        repository = self._require_transfers()
        transfer = await repository.get(transfer_id)
        if transfer.status not in {status.value for status in RESUMABLE_TRANSFER_STATUSES}:
            return self._transfer_schema(transfer)
        transfer.status = TransferStatus.QUEUED.value
        transfer.error = None
        await repository.save(transfer)
        await repository.commit()
        self._start(transfer.id)
        return self._transfer_schema(transfer)

    def _start(self, transfer_id: UUID) -> None:
        if self._tasks is None or self._session_factory is None or self._storage is None:
            raise RuntimeError("transfer execution is not configured")
        if self._fits_factory is None:
            raise RuntimeError("transfer execution is not configured")
        runner = TransferRunner(
            session_factory=self._session_factory,
            storage=self._storage,
            fits_factory=self._fits_factory,
            http_client_factory=self._http_client_factory,
        )
        self._tasks.start(str(transfer_id), lambda: runner(transfer_id))

    def _require_transfers(self) -> TransferRepository:
        if self._transfers is None:
            raise RuntimeError("transfer repository is not configured")
        return self._transfers

    def _candidate_schema(self, target_name: str, product: HubbleProduct) -> CandidateSchema:
        payload = {
            "target_name": target_name,
            "data_uri": product.data_uri,
            "product_filename": product.product_filename,
            "observation_id": product.observation_id,
            "proposal_id": product.proposal_id,
            "instrument": product.instrument,
            "filters": product.filters,
            "observed_at": product.observed_at,
            "size_bytes": product.size_bytes,
            "ra_deg": product.ra_deg,
            "dec_deg": product.dec_deg,
        }
        return CandidateSchema(
            token=sign_candidate_token(payload, self._token_secret),
            product_filename=product.product_filename,
            instrument=product.instrument,
            proposal_id=product.proposal_id,
            observation_id=product.observation_id,
            filters=product.filters,
            observed_at=product.observed_at,
            size_bytes=product.size_bytes,
            ra_deg=product.ra_deg,
            dec_deg=product.dec_deg,
            data_uri=product.data_uri,
        )

    def _transfer_schema(self, transfer: ImageTransfer) -> TransferStatusSchema:
        status = transfer.status
        return TransferStatusSchema(
            transfer_id=transfer.id,
            status=status,
            display_name=transfer.display_name,
            product_filename=transfer.product_filename,
            bytes_transferred=transfer.bytes_transferred,
            total_bytes=transfer.total_bytes,
            speed_bytes_per_second=transfer.speed_bytes_per_second,
            progress=progress_ratio(transfer.bytes_transferred, transfer.total_bytes),
            error=transfer.error,
            record_id=transfer.record_id,
            slug=transfer.slug,
            resumable=status in {item.value for item in RESUMABLE_TRANSFER_STATUSES},
        )
