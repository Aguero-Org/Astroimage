from __future__ import annotations

import time
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Path, Query, Response

from astroimage.render.deps import (
    preview_service_dependency,
    render_config_dependency,
    render_service_dependency,
)
from astroimage.render.preview import PreviewService
from astroimage.render.schema import HistogramResponse, RenderConfigSchema
from astroimage.render.service import RenderService
from astroimage.shared.query import HduIndex

router = APIRouter(prefix="/image", tags=["render"])
_log = structlog.get_logger("astroimage.render.controller")

RecordId = Annotated[
    UUID,
    Path(description="Stored FITS record id"),
]
BinsParam = Annotated[int, Query(ge=2, le=4096)]


@router.get(
    "/{record_id}",
    responses={200: {"content": {"image/png": {}}}},
    operation_id="renderFitsImage",
)
async def render_fits_image(
    record_id: RecordId,
    service: Annotated[RenderService, Depends(render_service_dependency)],
    config: Annotated[RenderConfigSchema, Depends(render_config_dependency)],
    hdu: HduIndex = None,
) -> Response:
    _log.info(
        "render_start",
        record_id=str(record_id),
        colormap=config.colormap,
        stretch=config.stretch,
    )
    start = time.perf_counter()
    png = await service.render_png_from_record(record_id, config=config, hdu_index=hdu)
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
    service: Annotated[PreviewService, Depends(preview_service_dependency)],
    size: Annotated[int, Query(description="Longest edge in pixels")] = 256,
) -> Response:
    png = await service.png(record_id, size)
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
