from __future__ import annotations

import time
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Path, Query, Request, Response

from astroimage.render.deps import render_service_dependency
from astroimage.render.preview_job import PREVIEW_EDGES, PreviewRenderer
from astroimage.render.schema import HistogramResponse, RenderConfigSchema
from astroimage.render.service import RenderService
from astroimage.shared.errors import BadRequestError
from astroimage.shared.query import HduIndex

router = APIRouter(prefix="/image", tags=["render"])
_DEFAULTS = RenderConfigSchema()
_log = structlog.get_logger("astroimage.render.controller")

RecordId = Annotated[
    UUID,
    Path(description="Stored FITS record id"),
]

StretchParam = Annotated[str, Query(pattern="^(linear|sqrt|log|asinh)$")]
LimitsParam = Annotated[str, Query(pattern="^(percentiles|zscale)$")]
ColormapParam = Annotated[str, Query(pattern="^(grey|inverse|heat|rainbow|cube_helix)$")]
PminParam = Annotated[float, Query(ge=0.0, lt=100.0)]
PmaxParam = Annotated[float, Query(gt=0.0, le=100.0)]
GammaParam = Annotated[float, Query(ge=0.1, le=5.0)]
BinsParam = Annotated[int, Query(ge=2, le=4096)]


def _config(
    stretch: str,
    limits: str,
    colormap: str,
    pmin: float,
    pmax: float,
    gamma: float,
) -> RenderConfigSchema:
    return RenderConfigSchema(
        stretch=stretch,
        limits=limits,
        colormap=colormap,
        pmin=pmin,
        pmax=pmax,
        gamma=gamma,
    )


@router.get(
    "/{record_id}",
    responses={200: {"content": {"image/png": {}}}},
    operation_id="renderFitsImage",
)
async def render_fits_image(
    record_id: RecordId,
    service: Annotated[RenderService, Depends(render_service_dependency)],
    hdu: HduIndex = None,
    stretch: StretchParam = _DEFAULTS.stretch,
    limits: LimitsParam = _DEFAULTS.limits,
    colormap: ColormapParam = _DEFAULTS.colormap,
    pmin: PminParam = _DEFAULTS.pmin,
    pmax: PmaxParam = _DEFAULTS.pmax,
    gamma: GammaParam = _DEFAULTS.gamma,
) -> Response:
    _log.info("render_start", record_id=str(record_id), colormap=colormap, stretch=stretch)
    start = time.perf_counter()
    png = await service.render_png_from_record(
        record_id,
        config=_config(stretch, limits, colormap, pmin, pmax, gamma),
        hdu_index=hdu,
    )
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    _log.info(
        "render_complete",
        record_id=str(record_id),
        png_bytes=len(png),
        elapsed_ms=elapsed_ms,
    )
    return Response(content=png, media_type="image/png")


@router.get(
    "/{record_id}/preview",
    responses={
        200: {"content": {"image/png": {}}},
        400: {"description": "Preview size is not available"},
        404: {"description": "FITS record not found"},
    },
    operation_id="getFitsPreview",
)
async def get_fits_preview(
    record_id: RecordId,
    request: Request,
    size: Annotated[int, Query(description="Longest edge in pixels")] = 256,
) -> Response:
    if size not in PREVIEW_EDGES:
        raise BadRequestError("Preview size is not available")
    renderer: PreviewRenderer | None = getattr(request.app.state, "preview_scheduler", None)
    if renderer is None:
        raise BadRequestError("Preview size is not available")
    png = await renderer.png(record_id, size)
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.get(
    "/{record_id}/histogram",
    response_model=HistogramResponse,
    operation_id="renderFitsHistogram",
)
async def render_fits_histogram(
    record_id: RecordId,
    service: Annotated[RenderService, Depends(render_service_dependency)],
    hdu: HduIndex = None,
    bins: BinsParam = 256,
) -> HistogramResponse:
    _log.info("histogram_start", record_id=str(record_id), bins=bins)
    start = time.perf_counter()
    result = await service.histogram_from_record(record_id, bins=bins, hdu_index=hdu)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    _log.info(
        "histogram_complete",
        record_id=str(record_id),
        elapsed_ms=elapsed_ms,
    )
    return result
