from __future__ import annotations

import asyncio
import io

import urllib3
from minio import Minio
from minio.error import MinioException, S3Error

from astroimage.config import Settings
from astroimage.shared.object_storage import ObjectStorageError

_CLIENT_ERRORS = (MinioException, urllib3.exceptions.HTTPError)


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
        try:
            await asyncio.to_thread(
                self._client.put_object,
                self._bucket,
                object_key,
                io.BytesIO(payload),
                len(payload),
                content_type=content_type,
            )
        except _CLIENT_ERRORS as exc:
            raise ObjectStorageError(str(exc)) from exc

    async def get_bytes(self, object_key: str) -> bytes:
        try:
            response = await asyncio.to_thread(self._client.get_object, self._bucket, object_key)
        except S3Error as exc:
            raise LookupError(f"object not found: {object_key}") from exc
        except _CLIENT_ERRORS as exc:
            raise ObjectStorageError(str(exc)) from exc
        try:
            return response.read()
        except _CLIENT_ERRORS as exc:
            raise ObjectStorageError(str(exc)) from exc
        finally:
            response.close()
            response.release_conn()

    async def list_object_keys(self, prefix: str) -> list[str]:
        try:
            objects = await asyncio.to_thread(
                self._client.list_objects,
                self._bucket,
                prefix=prefix,
                recursive=True,
            )
            return [obj.object_name for obj in objects]
        except _CLIENT_ERRORS as exc:
            raise ObjectStorageError(str(exc)) from exc

    async def remove(self, object_key: str) -> None:
        try:
            await asyncio.to_thread(self._client.remove_object, self._bucket, object_key)
        except _CLIENT_ERRORS as exc:
            raise ObjectStorageError(str(exc)) from exc
