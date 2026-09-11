from uuid import uuid4

import pytest

from astroimage.fits.model import FitsRecord
from astroimage.fits.repository import FitsRepository


def _record(*, object_key: str = "fits/sample.fits") -> FitsRecord:
    return FitsRecord(
        object_key=object_key,
        original_filename="sample.fits",
        size_bytes=32,
        metadata_payload={"source_name": "sample.fits"},
    )


@pytest.mark.asyncio
async def test_create_and_get(fits_repository: FitsRepository) -> None:
    created = await fits_repository.create(_record())
    loaded = await fits_repository.get(created.id)
    assert loaded.id == created.id
    assert loaded.object_key == "fits/sample.fits"
    assert loaded.metadata_payload["source_name"] == "sample.fits"


@pytest.mark.asyncio
async def test_get_missing_raises(fits_repository: FitsRepository) -> None:
    with pytest.raises(LookupError):
        await fits_repository.get(uuid4())


@pytest.mark.asyncio
async def test_get_by_object_key(fits_repository: FitsRepository) -> None:
    await fits_repository.create(_record(object_key="fits/lookup.fits"))
    found = await fits_repository.get_by_object_key("fits/lookup.fits")
    assert found.original_filename == "sample.fits"
    with pytest.raises(LookupError):
        await fits_repository.get_by_object_key("fits/missing.fits")


@pytest.mark.asyncio
async def test_list_returns_created_rows(fits_repository: FitsRepository) -> None:
    first = await fits_repository.create(_record(object_key="fits/a.fits"))
    second = await fits_repository.create(_record(object_key="fits/b.fits"))
    listed_ids = {row.id for row in await fits_repository.list(offset=0, limit=10)}
    assert listed_ids == {first.id, second.id}


@pytest.mark.asyncio
async def test_update_and_delete(fits_repository: FitsRepository) -> None:
    record = await fits_repository.create(_record())
    record.original_filename = "renamed.fits"
    updated = await fits_repository.update(record)
    assert updated.original_filename == "renamed.fits"

    await fits_repository.delete(updated)
    with pytest.raises(LookupError):
        await fits_repository.get(updated.id)
