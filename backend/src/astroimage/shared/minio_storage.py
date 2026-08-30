from __future__ import annotations

import asyncio
import io

from minio import Minio
from minio.error import S3Error

from astroimage.config import Settings


def create_object_storage_client(settings: Settings) -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


class MinioObjectStorage:
    def __init__(self, client: Minio, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    async def put_bytes(
        self,
        object_key: str,
        payload: bytes,
        *,
        content_type: str,
    ) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            self._bucket,
            object_key,
            io.BytesIO(payload),
            len(payload),
            content_type=content_type,
        )

    async def get_bytes(self, object_key: str) -> bytes:
        try:
            response = await asyncio.to_thread(self._client.get_object, self._bucket, object_key)
        except S3Error as exc:
            raise LookupError(f"object not found: {object_key}") from exc
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def remove(self, object_key: str) -> None:
        await asyncio.to_thread(self._client.remove_object, self._bucket, object_key)
