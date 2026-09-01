from typing import Annotated

from fastapi import Depends

from astroimage.fits.deps import fits_service_dependency
from astroimage.fits.service import FitsService
from astroimage.render.service import RenderService


def render_service_dependency(
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
) -> RenderService:
    return RenderService(fits=fits)
