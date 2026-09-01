from __future__ import annotations

import time
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from astroimage.sources.deps import source_service_dependency
from astroimage.sources.schema import PointDetectionConfigSchema, SourceDetectionResponse
from astroimage.sources.service import SourceDetectionService

router = APIRouter(prefix="/image", tags=["sources"])
_DEFAULTS = PointDetectionConfigSchema()
_log = structlog.get_logger("astroimage.sources.controller")

RecordId = Annotated[
    UUID,
    Path(description="Stored FITS record id"),
]
HduIndex = Annotated[
    int | None,
    Query(ge=0, description="Optional image HDU index; defaults to the first 2D image HDU"),
]

FwhmParam = Annotated[float, Query(ge=0.5)]
SigmaParam = Annotated[float, Query(ge=1.0)]
MinSnrParam = Annotated[float, Query(ge=0.0)]
MinScoreParam = Annotated[float, Query(ge=0.0, le=1.0)]
MinDistanceParam = Annotated[float, Query(ge=0.0)]
VisualWeightParam = Annotated[float, Query(ge=0.0, le=1.0)]
VisualAreaRadiusParam = Annotated[float, Query(ge=1.0)]
VisualAreaSigmaParam = Annotated[float, Query(ge=0.0)]
MaxSourcesParam = Annotated[int, Query(ge=0)]


def _config(
    fwhm: float,
    sigma: float,
    min_snr: float,
    min_score: float,
    min_distance: float,
    visual_weight: float,
    visual_area_radius: float,
    visual_area_sigma: float,
    max_sources: int,
) -> PointDetectionConfigSchema:
    return PointDetectionConfigSchema(
        fwhm=fwhm,
        sigma=sigma,
        min_snr=min_snr,
        min_score=min_score,
        min_distance=min_distance,
        visual_weight=visual_weight,
        visual_area_radius=visual_area_radius,
        visual_area_sigma=visual_area_sigma,
        max_sources=max_sources,
    )


@router.get(
    "/{record_id}/sources",
    response_model=SourceDetectionResponse,
    operation_id="detectSources",
)
async def detect_sources(
    record_id: RecordId,
    service: Annotated[SourceDetectionService, Depends(source_service_dependency)],
    hdu: HduIndex = None,
    fwhm: FwhmParam = _DEFAULTS.fwhm,
    sigma: SigmaParam = _DEFAULTS.sigma,
    min_snr: MinSnrParam = _DEFAULTS.min_snr,
    min_score: MinScoreParam = _DEFAULTS.min_score,
    min_distance: MinDistanceParam = _DEFAULTS.min_distance,
    visual_weight: VisualWeightParam = _DEFAULTS.visual_weight,
    visual_area_radius: VisualAreaRadiusParam = _DEFAULTS.visual_area_radius,
    visual_area_sigma: VisualAreaSigmaParam = _DEFAULTS.visual_area_sigma,
    max_sources: MaxSourcesParam = _DEFAULTS.max_sources,
) -> SourceDetectionResponse:
    _log.info(
        "detect_start",
        record_id=str(record_id),
        fwhm=fwhm,
        sigma=sigma,
        min_snr=min_snr,
    )
    start = time.perf_counter()
    try:
        result = await service.detect_from_record(
            record_id,
            hdu_index=hdu,
            config=_config(
                fwhm,
                sigma,
                min_snr,
                min_score,
                min_distance,
                visual_weight,
                visual_area_radius,
                visual_area_sigma,
                max_sources,
            ),
        )
    except LookupError as exc:
        _log.warning("detect_not_found", record_id=str(record_id))
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, OSError) as exc:
        _log.warning("detect_error", record_id=str(record_id), detail=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    _log.info(
        "detect_complete",
        record_id=str(record_id),
        point_count=len(result.point_sources),
        extended_count=len(result.extended_sources),
        elapsed_ms=elapsed_ms,
    )
    return service.to_schema(result)
