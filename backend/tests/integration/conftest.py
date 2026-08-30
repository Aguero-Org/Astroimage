from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from io import BytesIO

import numpy as np
import pytest
from astropy.io import fits
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from astroimage.config import Settings, get_settings
from astroimage.fits.model import FitsRecord
from astroimage.fits.reader import FitsReader
from astroimage.fits.repository import FitsRepository
from astroimage.fits.service import FitsService
from astroimage.fits.storage import FitsStorage
from astroimage.shared.database import Base, create_engine_from_settings, create_session_factory
from astroimage.shared.minio_storage import (
    MinioObjectStorage,
    create_object_storage_client,
    ensure_bucket,
)
from astroimage.shared.object_storage import ObjectStorage

_ = FitsRecord


def sample_fits_bytes(*, telescope: str = "KECK") -> bytes:
    data = np.ones((2, 3), dtype=float)
    hdu = fits.PrimaryHDU(data)
    hdu.header["TELESCOP"] = telescope
    buffer = BytesIO()
    hdu.writeto(buffer)
    return buffer.getvalue()


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture
def fits_bytes() -> bytes:
    return sample_fits_bytes(telescope="KECK")


@pytest.fixture
def other_fits_bytes() -> bytes:
    return sample_fits_bytes(telescope="HST")


@pytest.fixture
async def db_engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    engine = create_engine_from_settings(settings)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    factory = create_session_factory(db_engine)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    async with db_engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE fits_records RESTART IDENTITY CASCADE"))


@pytest.fixture
def object_storage(settings: Settings) -> Iterator[ObjectStorage]:
    client = create_object_storage_client(settings)
    ensure_bucket(client, settings.minio_bucket)
    storage = MinioObjectStorage(client, settings.minio_bucket)
    yield storage
    for obj in client.list_objects(settings.minio_bucket, recursive=True):
        object_name = obj.object_name
        if object_name is not None:
            client.remove_object(settings.minio_bucket, object_name)


@pytest.fixture
def fits_repository(db_session: AsyncSession) -> FitsRepository:
    return FitsRepository(db_session)


@pytest.fixture
def fits_storage(object_storage: ObjectStorage) -> FitsStorage:
    return FitsStorage(object_storage)


@pytest.fixture
def fits_service(fits_repository: FitsRepository, fits_storage: FitsStorage) -> FitsService:
    return FitsService(FitsReader(), fits_repository, fits_storage)
