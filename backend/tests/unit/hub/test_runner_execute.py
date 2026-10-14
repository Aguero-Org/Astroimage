from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Self
from uuid import UUID

import pytest

from astroimage.hub.mast_fetch import MastFetchError, ResourceProbe
from astroimage.hub.model import TransferStatus
from astroimage.hub.runner import TransferRunner
from astroimage.shared.object_storage import ObjectStorage

TRANSFER_ID = UUID("11111111-1111-1111-1111-111111111111")
RECORD_ID = UUID("44444444-4444-4444-4444-444444444444")


class _Session:
    def __init__(self, transfer: SimpleNamespace) -> None:
        self.transfer = transfer
        self.committed = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        return None

    def expunge(self, _obj: object) -> None:
        return None

    async def commit(self) -> None:
        self.committed += 1

    async def rollback(self) -> None:
        return None


class _Repository:
    def __init__(self, session: _Session, *, missing: bool = False) -> None:
        self._session = session
        self._missing = missing

    async def get(self, _transfer_id: UUID) -> SimpleNamespace:
        if self._missing:
            raise LookupError("gone")
        return self._session.transfer

    async def save(self, current: SimpleNamespace) -> None:
        self._session.transfer = current


class _Storage(ObjectStorage):
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.removed: list[str] = []

    async def put_bytes(
        self,
        object_key: str,
        payload: bytes,
        content_type: str | None = None,
    ) -> None:
        self.objects[object_key] = payload

    async def get_bytes(self, object_key: str) -> bytes:
        return self.objects[object_key]

    async def remove(self, object_key: str) -> None:
        self.removed.append(object_key)
        self.objects.pop(object_key, None)

    async def list_object_keys(self, prefix: str) -> list[str]:
        return [key for key in self.objects if key.startswith(prefix)]


class _Client:
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        return None


def _transfer(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "id": TRANSFER_ID,
        "status": TransferStatus.QUEUED.value,
        "target_name": "Andromeda",
        "display_name": "Andrómeda",
        "data_uri": "mast:HST/product",
        "product_filename": "product.fits",
        "observation_id": "obs",
        "proposal_id": "prop",
        "instrument": "WFC3",
        "filters": "F814W",
        "observed_at": "2020-01-01",
        "ra_deg": 10.0,
        "dec_deg": 41.0,
        "bytes_transferred": 0,
        "total_bytes": 4,
        "etag": None,
        "last_modified": None,
        "speed_bytes_per_second": None,
        "error": None,
        "record_id": None,
        "slug": None,
        "samples": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _runner(
    transfer: SimpleNamespace,
    storage: _Storage,
    monkeypatch: pytest.MonkeyPatch,
    *,
    missing: bool = False,
) -> TransferRunner:
    session = _Session(transfer)

    def session_factory() -> _Session:
        return session

    def repository(bound: _Session) -> _Repository:
        return _Repository(bound, missing=missing)

    stored: list[bytes] = []

    class _Fits:
        def __init__(self, _session: _Session) -> None:
            return None

        async def store_bytes(self, payload: bytes, **_kwargs: object) -> SimpleNamespace:
            stored.append(payload)
            return SimpleNamespace(id=RECORD_ID, slug="andromeda")

    monkeypatch.setattr("astroimage.hub.runner.TransferRepository", repository)
    runner = TransferRunner(
        session_factory=session_factory,  # type: ignore[arg-type]
        storage=storage,
        fits_factory=_Fits,  # type: ignore[arg-type]
        http_client_factory=_Client,  # type: ignore[arg-type]
    )
    runner.stored = stored  # type: ignore[attr-defined]
    return runner


def _patch_download(monkeypatch: pytest.MonkeyPatch, chunks: list[bytes]) -> None:
    async def probe(_client: object, _url: str) -> ResourceProbe:
        return ResourceProbe(
            total_bytes=4,
            etag="etag-1",
            last_modified="Mon",
            first_byte=b"x",
        )

    pending = list(chunks)

    async def read_range(_client: object, _url: str, _offset: int, _end: int) -> bytes:
        if not pending:
            return b""
        return pending.pop(0)

    monkeypatch.setattr("astroimage.hub.runner.probe_resource", probe)
    monkeypatch.setattr("astroimage.hub.runner.read_range", read_range)
    monkeypatch.setattr(
        "astroimage.hub.runner.annotate_fits_header",
        lambda payload, _target, _product: payload + b"-ann",
    )


@pytest.mark.asyncio
async def test_execute_stores_the_downloaded_fits(monkeypatch: pytest.MonkeyPatch) -> None:
    transfer = _transfer()
    storage = _Storage()
    runner = _runner(transfer, storage, monkeypatch)
    _patch_download(monkeypatch, [b"fits"])

    await runner(TRANSFER_ID)

    assert transfer.status == TransferStatus.COMPLETED.value
    assert transfer.record_id == RECORD_ID
    assert transfer.slug == "andromeda"
    assert runner.stored == [b"fits-ann"]  # type: ignore[attr-defined]
    assert transfer.bytes_transferred == 4


@pytest.mark.asyncio
async def test_execute_resets_when_the_remote_identity_is_gone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transfer = _transfer(bytes_transferred=4, total_bytes=4, etag="old")
    storage = _Storage()
    storage.objects[f"transfers/{TRANSFER_ID}/part-0000"] = b"stale"
    runner = _runner(transfer, storage, monkeypatch)

    async def probe(_client: object, _url: str) -> ResourceProbe:
        return ResourceProbe(total_bytes=4, etag=None, last_modified=None, first_byte=b"")

    async def read_range(_client: object, _url: str, _offset: int, _end: int) -> bytes:
        return b"fits"

    monkeypatch.setattr("astroimage.hub.runner.probe_resource", probe)
    monkeypatch.setattr("astroimage.hub.runner.read_range", read_range)
    monkeypatch.setattr(
        "astroimage.hub.runner.annotate_fits_header",
        lambda payload, _target, _product: payload,
    )

    await runner(TRANSFER_ID)

    assert f"transfers/{TRANSFER_ID}/part-0000" in storage.removed
    assert transfer.status == TransferStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_execute_stops_when_the_transfer_is_already_cancelled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transfer = _transfer(status=TransferStatus.CANCELLED.value)
    runner = _runner(transfer, _Storage(), monkeypatch)

    await runner(TRANSFER_ID)

    assert transfer.status == TransferStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_call_marks_fetch_errors_as_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    transfer = _transfer()
    runner = _runner(transfer, _Storage(), monkeypatch)

    async def probe(_client: object, _url: str) -> ResourceProbe:
        raise MastFetchError("mast down")

    monkeypatch.setattr("astroimage.hub.runner.probe_resource", probe)

    await runner(TRANSFER_ID)

    assert transfer.status == TransferStatus.FAILED.value
    assert transfer.error == "mast down"


@pytest.mark.asyncio
async def test_call_marks_cancellation_and_reraises(monkeypatch: pytest.MonkeyPatch) -> None:
    transfer = _transfer()
    runner = _runner(transfer, _Storage(), monkeypatch)

    async def probe(_client: object, _url: str) -> ResourceProbe:
        raise asyncio.CancelledError

    monkeypatch.setattr("astroimage.hub.runner.probe_resource", probe)

    with pytest.raises(asyncio.CancelledError):
        await runner(TRANSFER_ID)

    assert transfer.status == TransferStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_copy_stops_on_a_short_final_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    transfer = _transfer(total_bytes=None, bytes_transferred=0)
    storage = _Storage()
    runner = _runner(transfer, storage, monkeypatch)

    async def read_range(_client: object, _url: str, _offset: int, _end: int) -> bytes:
        return b"fits"

    monkeypatch.setattr("astroimage.hub.runner.read_range", read_range)

    await runner._copy_parts(_Client(), "https://example.test/product", transfer)  # type: ignore[arg-type]

    assert transfer.bytes_transferred == 4
    assert storage.objects


@pytest.mark.asyncio
async def test_copy_aborts_when_cancelled_between_parts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transfer = _transfer(total_bytes=8)
    runner = _runner(transfer, _Storage(), monkeypatch)

    async def probe(_client: object, _url: str) -> ResourceProbe:
        return ResourceProbe(total_bytes=8, etag="e", last_modified=None, first_byte=b"")

    async def read_range(_client: object, _url: str, _offset: int, _end: int) -> bytes:
        transfer.status = TransferStatus.CANCELLED.value
        return b"fits"

    monkeypatch.setattr("astroimage.hub.runner.probe_resource", probe)
    monkeypatch.setattr("astroimage.hub.runner.read_range", read_range)

    with pytest.raises(asyncio.CancelledError):
        await runner(TRANSFER_ID)

    assert transfer.status == TransferStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_finish_leaves_a_cancelled_transfer(monkeypatch: pytest.MonkeyPatch) -> None:
    transfer = _transfer()
    storage = _Storage()
    storage.objects[f"transfers/{TRANSFER_ID}/part-0000"] = b"fits"
    runner = _runner(transfer, storage, monkeypatch)

    async def load(_transfer_id: UUID) -> SimpleNamespace:
        transfer.status = TransferStatus.CANCELLED.value
        return transfer

    monkeypatch.setattr(runner, "_load", load)
    from astroimage.hub.importer import HubbleProduct

    await runner._finish(
        TRANSFER_ID,
        HubbleProduct(
            product_filename="product.fits",
            data_uri="mast:HST/product",
            size_bytes=4,
            observation_id="obs",
            proposal_id="prop",
            instrument="WFC3",
            ra_deg=10.0,
            dec_deg=41.0,
        ),
    )

    assert transfer.record_id is None


@pytest.mark.asyncio
async def test_record_progress_skips_a_cancelled_transfer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transfer = _transfer(status=TransferStatus.CANCELLED.value, samples=[[1.0, 1]])
    runner = _runner(transfer, _Storage(), monkeypatch)

    await runner._record_progress(TRANSFER_ID, 4)

    assert transfer.bytes_transferred == 0


@pytest.mark.asyncio
async def test_set_status_skips_a_cancelled_transfer(monkeypatch: pytest.MonkeyPatch) -> None:
    transfer = _transfer(status=TransferStatus.CANCELLED.value)
    runner = _runner(transfer, _Storage(), monkeypatch)

    await runner._set_status(TRANSFER_ID, TransferStatus.STORING)

    assert transfer.status == TransferStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_mark_ignores_a_missing_transfer(monkeypatch: pytest.MonkeyPatch) -> None:
    transfer = _transfer()
    runner = _runner(transfer, _Storage(), monkeypatch, missing=True)

    await runner._mark(TRANSFER_ID, TransferStatus.FAILED, error="x")

    assert transfer.status == TransferStatus.QUEUED.value


@pytest.mark.asyncio
async def test_mark_does_not_overwrite_cancellation(monkeypatch: pytest.MonkeyPatch) -> None:
    transfer = _transfer(status=TransferStatus.CANCELLED.value)
    runner = _runner(transfer, _Storage(), monkeypatch)

    await runner._mark(TRANSFER_ID, TransferStatus.FAILED, error="late")

    assert transfer.error is None


@pytest.mark.asyncio
async def test_read_parts_joins_every_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    from astroimage.hub.mast_fetch import PART_BYTES

    transfer = _transfer(bytes_transferred=PART_BYTES + 2)
    storage = _Storage()
    storage.objects[f"transfers/{TRANSFER_ID}/part-0000"] = b"ab"
    storage.objects[f"transfers/{TRANSFER_ID}/part-0001"] = b"cd"
    runner = _runner(transfer, storage, monkeypatch)

    payload = await runner._read_parts(transfer)  # type: ignore[arg-type]

    assert payload == b"abcd"
