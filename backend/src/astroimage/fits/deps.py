from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.preview_schedule import NullPreviewScheduler, PreviewScheduler
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


def preview_scheduler_from_request(request: Request) -> PreviewScheduler:
    scheduler = getattr(request.app.state, "preview_scheduler", None)
    if scheduler is None:
        return NullPreviewScheduler()
    return cast("PreviewScheduler", scheduler)


def fits_service_dependency(
    request: Request,
    reader: Annotated[FitsReader, Depends(FitsReader)],
    repository: Annotated[FitsRepository, Depends(fits_repository_dependency)],
    storage: Annotated[FitsStorage, Depends(fits_storage_dependency)],
) -> FitsService:
    return FitsService(
        reader,
        repository,
        storage,
        scheduler=preview_scheduler_from_request(request),
    )


def fits_service_from_resources(
    session: AsyncSession,
    objects: ObjectStorage,
    scheduler: PreviewScheduler | None = None,
) -> FitsService:
    return FitsService(
        FitsReader(),
        FitsRepository(session),
        FitsStorage(objects),
        scheduler=scheduler,
    )
