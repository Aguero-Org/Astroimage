from typing import Annotated

from fastapi import Depends

from astroimage.fits.deps import fits_service_dependency
from astroimage.fits.service import FitsService
from astroimage.sources.service import SourceDetectionService


def source_service_dependency(
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
) -> SourceDetectionService:
    return SourceDetectionService(fits=fits)
