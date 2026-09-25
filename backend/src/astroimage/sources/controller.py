from __future__ import annotations

import time
from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query

from astroimage.sources.deps import (
    gaia_background_dependency,
    gaia_job_registry_dependency,
    gaia_service_dependency,
    source_service_dependency,
)
from astroimage.sources.gaia_jobs import GaiaBackgroundVerify, GaiaJobRegistry, gaia_job_key
from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    GaiaJobStatusSchema,
    GaiaMatchConfigSchema,
    GaiaVerificationResponse,
    PointDetectionConfigSchema,
    SourceDetectionResponse,
)
from astroimage.sources.service import GaiaVerificationService, SourceDetectionService

router = APIRouter(prefix="/image", tags=["sources"])
_DEFAULTS = PointDetectionConfigSchema()
_EXTENDED_DEFAULTS = ExtendedDetectionConfigSchema()
_GAIA_DEFAULTS = GaiaMatchConfigSchema()
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
ExtendedSigmaParam = Annotated[float, Query(ge=0.5)]
ExtendedSmoothSigmaParam = Annotated[float, Query(ge=0.5)]
ExtendedMinAreaParam = Annotated[int, Query(ge=1)]
ExtendedMaxAreaParam = Annotated[int, Query(ge=0)]
ExtendedBinFactorParam = Annotated[int, Query(ge=1)]
ExtendedClosingIterationsParam = Annotated[int, Query(ge=0)]
ExtendedOpeningIterationsParam = Annotated[int, Query(ge=0)]
ExtendedMinScoreParam = Annotated[float, Query(ge=0.0, le=1.0)]
ExtendedMaxSourcesParam = Annotated[int, Query(ge=0)]
GaiaMatchRadiusParam = Annotated[float, Query(ge=0.0)]
GaiaProbabilityPowerParam = Annotated[float, Query(ge=0.1)]
GaiaJobId = Annotated[
    str,
    Path(min_length=1, description="Submission id returned by the gaia verification endpoint"),
]


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


def _extended_config(
    ext_sigma: float,
    ext_smooth_sigma: float,
    ext_min_area: int,
    ext_max_area: int,
    ext_bin_factor: int,
    ext_closing_iterations: int,
    ext_opening_iterations: int,
    ext_min_score: float,
    ext_max_sources: int,
) -> ExtendedDetectionConfigSchema:
    return ExtendedDetectionConfigSchema(
        sigma=ext_sigma,
        smooth_sigma=ext_smooth_sigma,
        min_area=ext_min_area,
        max_area=ext_max_area,
        bin_factor=ext_bin_factor,
        closing_iterations=ext_closing_iterations,
        opening_iterations=ext_opening_iterations,
        min_score=ext_min_score,
        max_sources=ext_max_sources,
    )


def _gaia_url(
    record_id: UUID,
    *,
    hdu: int | None,
    fwhm: float,
    sigma: float,
    min_snr: float,
    min_score: float,
    min_distance: float,
    visual_weight: float,
    visual_area_radius: float,
    visual_area_sigma: float,
    max_sources: int,
    ext_sigma: float,
    ext_smooth_sigma: float,
    ext_min_area: int,
    ext_max_area: int,
    ext_bin_factor: int,
    ext_closing_iterations: int,
    ext_opening_iterations: int,
    ext_min_score: float,
    ext_max_sources: int,
    match_radius_arcsec: float,
    probability_power: float,
) -> str:
    query = {
        "hdu": hdu,
        "fwhm": fwhm,
        "sigma": sigma,
        "min_snr": min_snr,
        "min_score": min_score,
        "min_distance": min_distance,
        "visual_weight": visual_weight,
        "visual_area_radius": visual_area_radius,
        "visual_area_sigma": visual_area_sigma,
        "max_sources": max_sources,
        "ext_sigma": ext_sigma,
        "ext_smooth_sigma": ext_smooth_sigma,
        "ext_min_area": ext_min_area,
        "ext_max_area": ext_max_area,
        "ext_bin_factor": ext_bin_factor,
        "ext_closing_iterations": ext_closing_iterations,
        "ext_opening_iterations": ext_opening_iterations,
        "ext_min_score": ext_min_score,
        "ext_max_sources": ext_max_sources,
        "match_radius_arcsec": match_radius_arcsec,
        "probability_power": probability_power,
    }
    query_string = urlencode({key: value for key, value in query.items() if value is not None})
    return f"/image/{record_id}/sources/gaia?{query_string}"


@router.get(
    "/{record_id}/sources",
    response_model=SourceDetectionResponse,
    operation_id="detectSources",
)
async def detect_sources(
    record_id: RecordId,
    service: Annotated[SourceDetectionService, Depends(source_service_dependency)],
    client_id: Annotated[str, Header(alias="X-Client-Id")] = "anonymous",
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
    ext_sigma: ExtendedSigmaParam = _EXTENDED_DEFAULTS.sigma,
    ext_smooth_sigma: ExtendedSmoothSigmaParam = _EXTENDED_DEFAULTS.smooth_sigma,
    ext_min_area: ExtendedMinAreaParam = _EXTENDED_DEFAULTS.min_area,
    ext_max_area: ExtendedMaxAreaParam = _EXTENDED_DEFAULTS.max_area,
    ext_bin_factor: ExtendedBinFactorParam = _EXTENDED_DEFAULTS.bin_factor,
    ext_closing_iterations: ExtendedClosingIterationsParam = (
        _EXTENDED_DEFAULTS.closing_iterations
    ),
    ext_opening_iterations: ExtendedOpeningIterationsParam = (
        _EXTENDED_DEFAULTS.opening_iterations
    ),
    ext_min_score: ExtendedMinScoreParam = _EXTENDED_DEFAULTS.min_score,
    ext_max_sources: ExtendedMaxSourcesParam = _EXTENDED_DEFAULTS.max_sources,
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
            client_id=client_id,
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
            extended_config=_extended_config(
                ext_sigma,
                ext_smooth_sigma,
                ext_min_area,
                ext_max_area,
                ext_bin_factor,
                ext_closing_iterations,
                ext_opening_iterations,
                ext_min_score,
                ext_max_sources,
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
    return service.to_schema(
        result,
        gaia_url=_gaia_url(
            record_id,
            hdu=hdu,
            fwhm=fwhm,
            sigma=sigma,
            min_snr=min_snr,
            min_score=min_score,
            min_distance=min_distance,
            visual_weight=visual_weight,
            visual_area_radius=visual_area_radius,
            visual_area_sigma=visual_area_sigma,
            max_sources=max_sources,
            ext_sigma=ext_sigma,
            ext_smooth_sigma=ext_smooth_sigma,
            ext_min_area=ext_min_area,
            ext_max_area=ext_max_area,
            ext_bin_factor=ext_bin_factor,
            ext_closing_iterations=ext_closing_iterations,
            ext_opening_iterations=ext_opening_iterations,
            ext_min_score=ext_min_score,
            ext_max_sources=ext_max_sources,
            match_radius_arcsec=_GAIA_DEFAULTS.match_radius_arcsec,
            probability_power=_GAIA_DEFAULTS.probability_power,
        ),
    )


@router.get(
    "/{record_id}/sources/gaia",
    response_model=GaiaVerificationResponse | GaiaJobStatusSchema,
    operation_id="verifySourcesGaia",
)
async def verify_sources_gaia(
    record_id: RecordId,
    service: Annotated[GaiaVerificationService, Depends(gaia_service_dependency)],
    background: Annotated[GaiaBackgroundVerify, Depends(gaia_background_dependency)],
    jobs: Annotated[GaiaJobRegistry, Depends(gaia_job_registry_dependency)],
    client_id: Annotated[str, Header(alias="X-Client-Id")] = "anonymous",
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
    ext_sigma: ExtendedSigmaParam = _EXTENDED_DEFAULTS.sigma,
    ext_smooth_sigma: ExtendedSmoothSigmaParam = _EXTENDED_DEFAULTS.smooth_sigma,
    ext_min_area: ExtendedMinAreaParam = _EXTENDED_DEFAULTS.min_area,
    ext_max_area: ExtendedMaxAreaParam = _EXTENDED_DEFAULTS.max_area,
    ext_bin_factor: ExtendedBinFactorParam = _EXTENDED_DEFAULTS.bin_factor,
    ext_closing_iterations: ExtendedClosingIterationsParam = (
        _EXTENDED_DEFAULTS.closing_iterations
    ),
    ext_opening_iterations: ExtendedOpeningIterationsParam = (
        _EXTENDED_DEFAULTS.opening_iterations
    ),
    ext_min_score: ExtendedMinScoreParam = _EXTENDED_DEFAULTS.min_score,
    ext_max_sources: ExtendedMaxSourcesParam = _EXTENDED_DEFAULTS.max_sources,
    match_radius_arcsec: GaiaMatchRadiusParam = _GAIA_DEFAULTS.match_radius_arcsec,
    probability_power: GaiaProbabilityPowerParam = _GAIA_DEFAULTS.probability_power,
) -> GaiaVerificationResponse | GaiaJobStatusSchema:
    detection_config = _config(
        fwhm,
        sigma,
        min_snr,
        min_score,
        min_distance,
        visual_weight,
        visual_area_radius,
        visual_area_sigma,
        max_sources,
    )
    extended_detection_config = _extended_config(
        ext_sigma,
        ext_smooth_sigma,
        ext_min_area,
        ext_max_area,
        ext_bin_factor,
        ext_closing_iterations,
        ext_opening_iterations,
        ext_min_score,
        ext_max_sources,
    )
    gaia_config = GaiaMatchConfigSchema(
        match_radius_arcsec=match_radius_arcsec,
        probability_power=probability_power,
    )
    _log.info(
        "gaia_verify_start",
        record_id=str(record_id),
        match_radius_arcsec=match_radius_arcsec,
        probability_power=probability_power,
    )
    key = gaia_job_key(
        record_id=record_id,
        client_id=client_id,
        hdu_index=hdu,
        config=detection_config,
        extended_config=extended_detection_config,
        gaia_config=gaia_config,
    )
    completed = jobs.get(key)
    if completed is not None:
        _log.info("gaia_verify_cache_hit", record_id=str(record_id))
        return completed
    try:
        await service.ensure_record(record_id)
    except LookupError as exc:
        _log.warning("gaia_verify_not_found", record_id=str(record_id))
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await jobs.start(
        key,
        lambda: background(
            record_id,
            client_id=client_id,
            hdu_index=hdu,
            config=detection_config,
            extended_config=extended_detection_config,
            gaia_config=gaia_config,
        ),
    )
    await jobs.wait(key)
    completed = jobs.get(key)
    if completed is not None:
        return completed
    failure = jobs.get_failure(key)
    if failure is not None:
        status_code, detail = failure
        raise HTTPException(status_code=status_code, detail=detail)
    raise HTTPException(status_code=500, detail="gaia verification did not complete")


@router.get(
    "/{record_id}/sources/gaia/jobs/{job_id}",
    response_model=GaiaVerificationResponse | GaiaJobStatusSchema,
    operation_id="getSourcesGaiaJob",
)
async def get_sources_gaia_job(
    record_id: RecordId,
    job_id: GaiaJobId,
    jobs: Annotated[GaiaJobRegistry, Depends(gaia_job_registry_dependency)],
) -> GaiaVerificationResponse | GaiaJobStatusSchema:
    completed = jobs.get(job_id)
    if completed is not None:
        return completed
    if jobs.is_running(job_id):
        return GaiaJobStatusSchema(job_id=job_id, record_id=record_id)
    failure = jobs.get_failure(job_id)
    if failure is not None:
        status_code, detail = failure
        raise HTTPException(status_code=status_code, detail=detail)
    raise HTTPException(status_code=404, detail=f"Unknown Gaia job: {job_id}")
