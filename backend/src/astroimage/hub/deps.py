from typing import Annotated

from fastapi import Depends

from astroimage.fits.deps import fits_service_dependency
from astroimage.fits.service import FitsService
from astroimage.hub.importer import HubbleImporter
from astroimage.hub.service import HubbleImageService


def hubble_importer_dependency() -> HubbleImporter:
    return HubbleImporter()


def hubble_service_dependency(
    importer: Annotated[HubbleImporter, Depends(hubble_importer_dependency)],
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
) -> HubbleImageService:
    return HubbleImageService(importer, fits)
