from __future__ import annotations

from typing import Protocol


class ObjectStorage(Protocol):
    async def put_bytes(
        self,
        object_key: str,
        payload: bytes,
        *,
        content_type: str,
    ) -> None: ...

    async def get_bytes(self, object_key: str) -> bytes: ...

    async def remove(self, object_key: str) -> None: ...
