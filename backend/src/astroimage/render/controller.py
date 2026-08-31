from __future__ import annotations

import time
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response

from astroimage.render.deps import render_service_dependency
from astroimage.render.schema import HistogramResponse, RenderConfigSchema
from astroimage.render.service import RenderService

router = APIRouter(prefix="/image", tags=["render"])
_DEFAULTS = RenderConfigSchema()
_log = structlog.get_logger("astroimage.render.controller")

RecordId = Annotated[
    UUID,
    Path(description="Stored FITS record id"),
]
HduIndex = Annotated[
    int | None,
    Query(ge=0, description="Optional image HDU index; defaults to the first 2D image HDU"),
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
    try:
        png = await service.render_png_from_record(
            record_id,
            config=_config(stretch, limits, colormap, pmin, pmax, gamma),
            hdu_index=hdu,
        )
    except LookupError as exc:
        _log.warning("render_not_found", record_id=str(record_id))
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, OSError) as exc:
        _log.warning("render_error", record_id=str(record_id), detail=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    _log.info(
        "render_complete",
        record_id=str(record_id),
        png_bytes=len(png),
        elapsed_ms=elapsed_ms,
    )
    return Response(content=png, media_type="image/png")


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
    try:
        result = await service.histogram_from_record(record_id, bins=bins, hdu_index=hdu)
    except LookupError as exc:
        _log.warning("histogram_not_found", record_id=str(record_id))
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, OSError) as exc:
        _log.warning("histogram_error", record_id=str(record_id), detail=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    _log.info(
        "histogram_complete",
        record_id=str(record_id),
        elapsed_ms=elapsed_ms,
    )
    return result
