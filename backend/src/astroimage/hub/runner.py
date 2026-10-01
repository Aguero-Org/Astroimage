from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from uuid import UUID

import httpx
import structlog
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from astroimage.fits.service import FitsService
from astroimage.hub.importer import HubbleProduct, annotate_fits_header, mast_download_url
from astroimage.hub.mast_fetch import (
    PART_BYTES,
    ResourceProbe,
    can_resume,
    identity_changed,
    probe_resource,
    read_range,
)
from astroimage.hub.model import ImageTransfer, TransferStatus
from astroimage.hub.progress import moving_average_bytes_per_second
from astroimage.hub.repository import TransferRepository
from astroimage.hub.slug import product_slug
from astroimage.shared.object_storage import ObjectStorage

_log = structlog.get_logger("astroimage.hub.runner")
_tracer = trace.get_tracer("astroimage.hub.runner")

FitsFactory = Callable[[AsyncSession], FitsService]


def part_key(transfer_id: UUID, index: int) -> str:
    return f"transfers/{transfer_id}/part-{index:04d}"


class TransferRunner:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        storage: ObjectStorage,
        fits_factory: FitsFactory,
        http_client_factory: Callable[[], httpx.AsyncClient],
    ) -> None:
        self._session_factory = session_factory
        self._storage = storage
        self._fits_factory = fits_factory
        self._http_client_factory = http_client_factory

    async def __call__(self, transfer_id: UUID) -> None:
        try:
            await self._execute(transfer_id)
        except asyncio.CancelledError:
            await self._mark(transfer_id, TransferStatus.CANCELLED, error=None)
            raise
        except Exception as exc:
            _log.exception("transfer_failed", transfer_id=str(transfer_id))
            await self._mark(transfer_id, TransferStatus.FAILED, error=str(exc))

    async def _execute(self, transfer_id: UUID) -> None:
        transfer = await self._load(transfer_id)
        if transfer.status == TransferStatus.CANCELLED.value:
            return
        product = _product_from_transfer(transfer)
        url = mast_download_url(product.data_uri)
        async with self._http_client_factory() as client:
            with _tracer.start_as_current_span("mast_transfer") as span:
                span.set_attribute("data_uri", product.data_uri)
                await self._set_status(transfer_id, TransferStatus.TRANSFERRING)
                probe = await probe_resource(client, url)
                transfer = await self._load(transfer_id)
                validators_missing = not probe.etag and not probe.last_modified
                if transfer.bytes_transferred > 0 and (
                    not can_resume(probe, bytes_transferred=transfer.bytes_transferred)
                    or validators_missing
                    or identity_changed(
                        stored_etag=transfer.etag,
                        stored_last_modified=transfer.last_modified,
                        stored_total=transfer.total_bytes,
                        probe=probe,
                    )
                ):
                    await self._reset_parts(transfer)
                    transfer = await self._load(transfer_id)
                await self._store_identity(transfer_id, probe)
                transfer = await self._load(transfer_id)
                await self._copy_parts(client, url, transfer)
        await self._finish(transfer_id, product)

    async def _copy_parts(
        self,
        client: httpx.AsyncClient,
        url: str,
        transfer: ImageTransfer,
    ) -> None:
        offset = transfer.bytes_transferred
        total = transfer.total_bytes
        part_index = offset // PART_BYTES
        while total is None or offset < total:
            if await self._is_cancelled(transfer.id):
                raise asyncio.CancelledError
            end = offset + PART_BYTES - 1
            if total is not None:
                end = min(end, total - 1)
            chunk = await read_range(client, url, offset, end)
            if chunk == b"":
                break
            await self._storage.put_bytes(
                part_key(transfer.id, part_index),
                chunk,
                content_type="application/octet-stream",
            )
            offset += len(chunk)
            part_index += 1
            await self._record_progress(transfer.id, offset)
            if total is not None and offset >= total:
                break
            if len(chunk) < PART_BYTES and total is None:
                break

    async def _finish(self, transfer_id: UUID, product: HubbleProduct) -> None:
        transfer = await self._load(transfer_id)
        if transfer.status == TransferStatus.CANCELLED.value:
            return
        await self._set_status(transfer_id, TransferStatus.ANNOTATING)
        payload = await self._read_parts(transfer)
        target_name = transfer.target_name
        annotated = annotate_fits_header(payload, target_name, product)
        await self._set_status(transfer_id, TransferStatus.STORING)
        slug = product_slug(
            target_name=target_name,
            instrument=transfer.instrument,
            proposal_id=transfer.proposal_id,
            observation_id=transfer.observation_id,
            data_uri=transfer.data_uri,
        )
        provenance = {
            "data_uri": transfer.data_uri,
            "observation_id": transfer.observation_id,
            "proposal_id": transfer.proposal_id,
            "instrument": transfer.instrument,
            "filters": transfer.filters,
            "observed_at": transfer.observed_at,
            "size_bytes": transfer.total_bytes,
            "display_name": transfer.display_name,
        }
        async with self._session_factory() as session:
            fits = self._fits_factory(session)
            record = await fits.store_bytes(
                annotated,
                source_name=target_name,
                analyze=True,
                slug=slug,
                original_filename=transfer.product_filename,
                provenance=provenance,
            )
            repository = TransferRepository(session)
            current = await repository.get(transfer_id)
            current.status = TransferStatus.COMPLETED.value
            current.record_id = record.id
            current.slug = record.slug
            current.error = None
            await repository.save(current)
            await session.commit()
        _log.info("transfer_completed", transfer_id=str(transfer_id), record_id=str(record.id))

    async def _read_parts(self, transfer: ImageTransfer) -> bytes:
        chunks: list[bytes] = []
        part_count = max(1, (transfer.bytes_transferred + PART_BYTES - 1) // PART_BYTES)
        for index in range(part_count):
            chunks.append(await self._storage.get_bytes(part_key(transfer.id, index)))
        return b"".join(chunks)

    async def _reset_parts(self, transfer: ImageTransfer) -> None:
        keys = await self._storage.list_object_keys(f"transfers/{transfer.id}/")
        for key in keys:
            await self._storage.remove(key)
        async with self._session_factory() as session:
            repository = TransferRepository(session)
            current = await repository.get(transfer.id)
            current.bytes_transferred = 0
            current.samples = []
            await repository.save(current)
            await session.commit()

    async def _store_identity(self, transfer_id: UUID, probe: ResourceProbe) -> None:
        async with self._session_factory() as session:
            repository = TransferRepository(session)
            current = await repository.get(transfer_id)
            current.etag = probe.etag
            current.last_modified = probe.last_modified
            current.total_bytes = probe.total_bytes
            await repository.save(current)
            await session.commit()

    async def _record_progress(self, transfer_id: UUID, offset: int) -> None:
        now = time.time()
        async with self._session_factory() as session:
            repository = TransferRepository(session)
            current = await repository.get(transfer_id)
            if current.status == TransferStatus.CANCELLED.value:
                await session.rollback()
                return
            samples = list(current.samples or [])
            samples.append([now, offset])
            current.samples = samples[-30:]
            current.bytes_transferred = offset
            typed = [(float(item[0]), int(item[1])) for item in current.samples]
            current.speed_bytes_per_second = moving_average_bytes_per_second(typed, now=now)
            await repository.save(current)
            await session.commit()

    async def _load(self, transfer_id: UUID) -> ImageTransfer:
        async with self._session_factory() as session:
            transfer = await TransferRepository(session).get(transfer_id)
            session.expunge(transfer)
            return transfer

    async def _is_cancelled(self, transfer_id: UUID) -> bool:
        transfer = await self._load(transfer_id)
        return transfer.status == TransferStatus.CANCELLED.value

    async def _set_status(self, transfer_id: UUID, status: TransferStatus) -> None:
        async with self._session_factory() as session:
            repository = TransferRepository(session)
            current = await repository.get(transfer_id)
            if current.status == TransferStatus.CANCELLED.value:
                await session.rollback()
                return
            current.status = status.value
            await repository.save(current)
            await session.commit()

    async def _mark(self, transfer_id: UUID, status: TransferStatus, *, error: str | None) -> None:
        async with self._session_factory() as session:
            repository = TransferRepository(session)
            try:
                current = await repository.get(transfer_id)
            except LookupError:
                return
            if status is TransferStatus.FAILED and current.status == TransferStatus.CANCELLED.value:
                return
            current.status = status.value
            current.error = error
            await repository.save(current)
            await session.commit()


def _product_from_transfer(transfer: ImageTransfer) -> HubbleProduct:
    return HubbleProduct(
        product_filename=transfer.product_filename,
        data_uri=transfer.data_uri,
        size_bytes=transfer.total_bytes,
        observation_id=transfer.observation_id,
        proposal_id=transfer.proposal_id,
        instrument=transfer.instrument,
        ra_deg=transfer.ra_deg,
        dec_deg=transfer.dec_deg,
    )
