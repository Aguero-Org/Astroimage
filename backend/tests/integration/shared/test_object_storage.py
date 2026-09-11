from uuid import uuid4

import pytest

from astroimage.config import Settings
from astroimage.shared.minio_storage import create_object_storage_client, ensure_bucket
from astroimage.shared.object_storage import ObjectStorage


def test_create_object_storage_client_and_bucket(settings: Settings) -> None:
    client = create_object_storage_client(settings)
    ensure_bucket(client, settings.minio_bucket)
    assert client.bucket_exists(settings.minio_bucket)


def test_ensure_bucket_creates_missing_bucket(settings: Settings) -> None:
    client = create_object_storage_client(settings)
    bucket = f"ai-test-{uuid4().hex[:12]}"
    try:
        assert client.bucket_exists(bucket) is False
        ensure_bucket(client, bucket)
        assert client.bucket_exists(bucket) is True
        ensure_bucket(client, bucket)
        assert client.bucket_exists(bucket) is True
    finally:
        if client.bucket_exists(bucket):
            client.remove_bucket(bucket)


@pytest.mark.asyncio
async def test_object_storage_put_get_remove(object_storage: ObjectStorage) -> None:
    await object_storage.put_bytes("fits/a.fits", b"payload", content_type="application/fits")
    assert await object_storage.get_bytes("fits/a.fits") == b"payload"
    await object_storage.remove("fits/a.fits")
    with pytest.raises(LookupError):
        await object_storage.get_bytes("fits/a.fits")
