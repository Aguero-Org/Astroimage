from pathlib import Path
from uuid import uuid4

import numpy as np
import pytest
from astropy.io import fits

from astroimage.fits.service import FitsService
from astroimage.fits.storage import FitsStorage


def test_metadata_from_path_and_schema(fits_service: FitsService, tmp_path: Path) -> None:
    fits_path = tmp_path / "keck.fits"
    data = np.ones((2, 3), dtype=float)
    hdu = fits.PrimaryHDU(data)
    hdu.header["TELESCOP"] = "KECK"
    hdu.writeto(fits_path, overwrite=True)

    model = fits_service.metadata_from_path(fits_path)
    schema = fits_service.to_schema(model)
    assert model.instrument.telescope == "KECK"
    assert schema.instrument.telescope == "KECK"
    assert schema.image.shape == [2, 3]


@pytest.mark.asyncio
async def test_store_get_list_and_payload(
    fits_service: FitsService,
    fits_bytes: bytes,
) -> None:
    record = await fits_service.store_bytes(fits_bytes, source_name="keck.fits")

    loaded = await fits_service.get_record(record.id)
    assert loaded.object_key.startswith("fits/")
    assert loaded.object_key.endswith(".fits")
    assert loaded.original_filename == "keck.fits"
    assert loaded.size_bytes == len(fits_bytes)
    assert loaded.metadata_payload["instrument"]["telescope"] == "KECK"
    assert await fits_service.get_payload(loaded) == fits_bytes

    listed = await fits_service.list_records()
    assert listed[0].id == record.id


@pytest.mark.asyncio
async def test_replace_bytes_updates_object_and_row(
    fits_service: FitsService,
    fits_bytes: bytes,
    other_fits_bytes: bytes,
) -> None:
    record = await fits_service.store_bytes(fits_bytes, source_name="old.fits")

    updated = await fits_service.replace_bytes(
        record.id,
        other_fits_bytes,
        source_name="hst.fits",
    )
    assert updated.original_filename == "hst.fits"
    assert updated.size_bytes == len(other_fits_bytes)
    assert updated.metadata_payload["instrument"]["telescope"] == "HST"
    assert await fits_service.get_payload(updated) == other_fits_bytes


@pytest.mark.asyncio
async def test_delete_record_removes_row_and_object(
    fits_service: FitsService,
    fits_storage: FitsStorage,
    fits_bytes: bytes,
) -> None:
    record = await fits_service.store_bytes(fits_bytes, source_name="keck.fits")
    object_key = record.object_key
    await fits_service.delete_record(record.id)
    with pytest.raises(LookupError):
        await fits_service.get_record(record.id)
    with pytest.raises(LookupError):
        await fits_storage.get(object_key)


@pytest.mark.asyncio
async def test_delete_missing_record_raises(fits_service: FitsService) -> None:
    with pytest.raises(LookupError):
        await fits_service.delete_record(uuid4())


@pytest.mark.asyncio
async def test_replace_missing_record_raises(
    fits_service: FitsService,
    fits_bytes: bytes,
) -> None:
    with pytest.raises(LookupError):
        await fits_service.replace_bytes(uuid4(), fits_bytes, source_name="keck.fits")
