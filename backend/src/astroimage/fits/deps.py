from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.reader import FitsReader
from astroimage.fits.repository import FitsRepository
from astroimage.fits.service import FitsService
from astroimage.fits.storage import FitsStorage
from astroimage.shared.deps import db_session_dependency, object_storage_dependency
from astroimage.shared.object_storage import ObjectStorage


def fits_repository_dependency(
    session: Annotated[AsyncSession, Depends(db_session_dependency)],
) -> FitsRepository:
    return FitsRepository(session)


def fits_storage_dependency(
    objects: Annotated[ObjectStorage, Depends(object_storage_dependency)],
) -> FitsStorage:
    return FitsStorage(objects)


def fits_service_dependency(
    reader: Annotated[FitsReader, Depends(FitsReader)],
    repository: Annotated[FitsRepository, Depends(fits_repository_dependency)],
    storage: Annotated[FitsStorage, Depends(fits_storage_dependency)],
) -> FitsService:
    return FitsService(reader, repository, storage)
