from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from astroimage.sources.schema import PointDetectionConfigSchema, SourceDetectionResponse
from astroimage.sources.service import SourceDetectionService

router = APIRouter(prefix="/sources", tags=["sources"])
_service = SourceDetectionService()
_DEFAULTS = PointDetectionConfigSchema()

SourceFile = Annotated[UploadFile, File(description="FITS file to analyze")]
HduIndex = Annotated[
    int | None,
    Query(ge=0, description="Optional image HDU index; defaults to the first 2D image HDU"),
]

FwhmParam = Annotated[float, Form(ge=0.5)]
SigmaParam = Annotated[float, Form(ge=1.0)]
MinSnrParam = Annotated[float, Form(ge=0.0)]
MinScoreParam = Annotated[float, Form(ge=0.0, le=1.0)]
MinDistanceParam = Annotated[float, Form(ge=0.0)]
VisualWeightParam = Annotated[float, Form(ge=0.0, le=1.0)]
VisualAreaRadiusParam = Annotated[float, Form(ge=1.0)]
VisualAreaSigmaParam = Annotated[float, Form(ge=0.0)]
MaxSourcesParam = Annotated[int, Form(ge=0)]


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


@router.post(
    "/detect",
    response_model=SourceDetectionResponse,
    operation_id="detectSources",
)
async def detect_sources(
    file: SourceFile,
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
    payload = await file.read()
    try:
        result = _service.detect(
            payload,
            source_name=file.filename,
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
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _service.to_schema(result)
