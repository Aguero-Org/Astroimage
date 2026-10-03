from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.deps import fits_service_dependency, fits_service_from_resources
from astroimage.fits.service import FitsService
from astroimage.hub.importer import HubbleImporter
from astroimage.hub.repository import TransferRepository
from astroimage.hub.service import HubbleImageService
from astroimage.shared.background import BackgroundTasks
from astroimage.shared.deps import (
    db_session_dependency,
    object_storage_dependency,
)
from astroimage.shared.object_storage import ObjectStorage


def hubble_importer_dependency() -> HubbleImporter:
    return HubbleImporter()


def hubble_service_dependency(
    request: Request,
    importer: Annotated[HubbleImporter, Depends(hubble_importer_dependency)],
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
    session: Annotated[AsyncSession, Depends(db_session_dependency)],
    storage: Annotated[ObjectStorage, Depends(object_storage_dependency)],
) -> HubbleImageService:
    tasks: BackgroundTasks = request.app.state.background_tasks
    return HubbleImageService(
        importer,
        fits,
        transfers=TransferRepository(session),
        tasks=tasks,
        session_factory=request.app.state.session_factory,
        storage=storage,
        token_secret=request.app.state.settings.candidate_token_secret,
        fits_factory=lambda db_session: fits_service_from_resources(db_session, storage),
    )
