from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from astroimage.shared.object_storage import ObjectStorage

_FITS_CONTENT_TYPE = "application/fits"
_OBJECT_PREFIX = "fits/"


class FitsStorage:
    def __init__(self, objects: ObjectStorage) -> None:
        self._objects = objects

    def new_object_key(self, source_name: str) -> str:
        suffix = Path(source_name).suffix or ".fits"
        return f"{_OBJECT_PREFIX}{uuid4()}{suffix}"

    async def put(self, payload: bytes, *, source_name: str) -> str:
        object_key = self.new_object_key(source_name)
        await self.put_at(object_key, payload)
        return object_key

    async def put_at(self, object_key: str, payload: bytes) -> None:
        await self._objects.put_bytes(object_key, payload, content_type=_FITS_CONTENT_TYPE)

    async def get(self, object_key: str) -> bytes:
        return await self._objects.get_bytes(object_key)

    async def remove(self, object_key: str) -> None:
        await self._objects.remove(object_key)
