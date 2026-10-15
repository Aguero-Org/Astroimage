from __future__ import annotations

from uuid import UUID

import pytest

from astroimage.hub.runner import TransferRunner
from astroimage.shared.object_storage import ObjectStorage, ObjectStorageError


class _Storage(ObjectStorage):
    def __init__(self, keys: list[str], *, fail: Exception | None = None) -> None:
        self.keys = keys
        self.fail = fail
        self.removed: list[str] = []
        self.puts: list[str] = []

    async def put_bytes(
        self,
        object_key: str,
        payload: bytes,
        content_type: str | None = None,
    ) -> None:
        self.puts.append(object_key)

    async def get_bytes(self, object_key: str) -> bytes:
        raise AssertionError("not used")

    async def remove(self, object_key: str) -> None:
        if self.fail is not None:
            raise self.fail
        self.removed.append(object_key)

    async def list_object_keys(self, prefix: str) -> list[str]:
        return [key for key in self.keys if key.startswith(prefix)]


def _runner(storage: ObjectStorage) -> TransferRunner:
    return TransferRunner(
        session_factory=None,  # type: ignore[arg-type]
        storage=storage,
        fits_factory=None,  # type: ignore[arg-type]
        http_client_factory=None,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_purge_parts_removes_every_chunk_of_the_transfer() -> None:
    transfer_id = UUID("11111111-1111-1111-1111-111111111111")
    other = UUID("22222222-2222-2222-2222-222222222222")
    storage = _Storage(
        [
            f"transfers/{transfer_id}/part-0000",
            f"transfers/{transfer_id}/part-0001",
            f"transfers/{other}/part-0000",
            "fits/keep-me.fits",
        ]
    )

    await _runner(storage)._purge_parts(transfer_id)

    assert storage.removed == [
        f"transfers/{transfer_id}/part-0000",
        f"transfers/{transfer_id}/part-0001",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "storage_error",
    [OSError("minio unreachable"), ObjectStorageError("minio unreachable")],
)
async def test_purge_parts_swallows_storage_errors(storage_error: Exception) -> None:
    transfer_id = UUID("33333333-3333-3333-3333-333333333333")
    storage = _Storage([f"transfers/{transfer_id}/part-0000"], fail=storage_error)

    await _runner(storage)._purge_parts(transfer_id)

    assert storage.removed == []
