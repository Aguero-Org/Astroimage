from uuid import uuid4

import pytest

from astroimage.fits.storage import FitsStorage


@pytest.mark.asyncio
async def test_put_get_remove_roundtrip(fits_storage: FitsStorage, fits_bytes: bytes) -> None:
    object_key = await fits_storage.put(fits_bytes, source_name="keck.fits")
    assert object_key.startswith("fits/")
    assert object_key.endswith(".fits")
    assert await fits_storage.get(object_key) == fits_bytes
    await fits_storage.remove(object_key)
    with pytest.raises(LookupError):
        await fits_storage.get(object_key)


@pytest.mark.asyncio
async def test_put_at_overwrites(
    fits_storage: FitsStorage,
    fits_bytes: bytes,
    other_fits_bytes: bytes,
) -> None:
    object_key = "fits/overwrite.fits"
    await fits_storage.put_at(object_key, fits_bytes)
    await fits_storage.put_at(object_key, other_fits_bytes)
    assert await fits_storage.get(object_key) == other_fits_bytes


def test_new_object_key_without_suffix(fits_storage: FitsStorage) -> None:
    key = fits_storage.new_object_key("no-extension")
    assert key.startswith("fits/")
    assert key.endswith(".fits")


def test_object_key_for_uses_record_id(fits_storage: FitsStorage) -> None:
    key = fits_storage.object_key_for(uuid4(), "hst.fits")
    assert key.startswith("fits/")
    assert key.endswith(".fits")
