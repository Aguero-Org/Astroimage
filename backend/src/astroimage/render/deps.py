from typing import Annotated, cast

from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.deps import fits_service_dependency
from astroimage.fits.reader import FitsReader
from astroimage.fits.service import FitsService
from astroimage.render.preview import PreviewService
from astroimage.render.schema import RenderConfigSchema
from astroimage.render.service import RenderService
from astroimage.shared.deps import db_session_dependency

StretchParam = Annotated[str, Query(pattern="^(linear|sqrt|log|asinh)$")]
LimitsParam = Annotated[str, Query(pattern="^(percentiles|zscale)$")]
ColormapParam = Annotated[
    str,
    Query(pattern="^(grey|inverse|heat|rainbow|cube_helix)$"),
]
PminParam = Annotated[float, Query(ge=0.0, lt=100.0)]
PmaxParam = Annotated[float, Query(gt=0.0, le=100.0)]
GammaParam = Annotated[float, Query(ge=0.1, le=5.0)]


def render_config_dependency(
    stretch: StretchParam = "sqrt",
    limits: LimitsParam = "percentiles",
    colormap: ColormapParam = "grey",
    pmin: PminParam = 1.0,
    pmax: PmaxParam = 99.0,
    gamma: GammaParam = 1.0,
) -> RenderConfigSchema:
    return RenderConfigSchema.model_validate(
        {
            "stretch": stretch,
            "limits": limits,
            "colormap": colormap,
            "pmin": pmin,
            "pmax": pmax,
            "gamma": gamma,
        }
    )


def render_service_dependency(
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
    reader: Annotated[FitsReader, Depends(FitsReader)],
) -> RenderService:
    return RenderService(reader, fits)


def preview_service_dependency(
    request: Request,
    session: Annotated[AsyncSession, Depends(db_session_dependency)],
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
    reader: Annotated[FitsReader, Depends(FitsReader)],
) -> PreviewService:
    scheduler = cast(PreviewService, request.app.state.preview_scheduler)
    return scheduler.for_request(session, reader, fits)
