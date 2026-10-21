from __future__ import annotations

import time
from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, Path, Query

from astroimage.shared.errors import InternalServerError, NotFoundError
from astroimage.shared.query import HduIndex
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
    SourcePresetResponse,
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


def point_detection_query(
    fwhm: FwhmParam = _DEFAULTS.fwhm,
    sigma: SigmaParam = _DEFAULTS.sigma,
    min_snr: MinSnrParam = _DEFAULTS.min_snr,
    min_score: MinScoreParam = _DEFAULTS.min_score,
    min_distance: MinDistanceParam = _DEFAULTS.min_distance,
    visual_weight: VisualWeightParam = _DEFAULTS.visual_weight,
    visual_area_radius: VisualAreaRadiusParam = _DEFAULTS.visual_area_radius,
    visual_area_sigma: VisualAreaSigmaParam = _DEFAULTS.visual_area_sigma,
    max_sources: MaxSourcesParam = _DEFAULTS.max_sources,
) -> PointDetectionConfigSchema:
    return _config(
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


def extended_detection_query(
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
) -> ExtendedDetectionConfigSchema:
    return _extended_config(
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


def gaia_match_query(
    match_radius_arcsec: GaiaMatchRadiusParam = _GAIA_DEFAULTS.match_radius_arcsec,
    probability_power: GaiaProbabilityPowerParam = _GAIA_DEFAULTS.probability_power,
) -> GaiaMatchConfigSchema:
    return GaiaMatchConfigSchema(
        match_radius_arcsec=match_radius_arcsec,
        probability_power=probability_power,
    )


def _gaia_url(
    record_id: UUID,
    *,
    hdu: int | None,
    config: PointDetectionConfigSchema,
    extended_config: ExtendedDetectionConfigSchema,
    gaia_config: GaiaMatchConfigSchema,
) -> str:
    query = {
        "hdu": hdu,
        "fwhm": config.fwhm,
        "sigma": config.sigma,
        "min_snr": config.min_snr,
        "min_score": config.min_score,
        "min_distance": config.min_distance,
        "visual_weight": config.visual_weight,
        "visual_area_radius": config.visual_area_radius,
        "visual_area_sigma": config.visual_area_sigma,
        "max_sources": config.max_sources,
        "ext_sigma": extended_config.sigma,
        "ext_smooth_sigma": extended_config.smooth_sigma,
        "ext_min_area": extended_config.min_area,
        "ext_max_area": extended_config.max_area,
        "ext_bin_factor": extended_config.bin_factor,
        "ext_closing_iterations": extended_config.closing_iterations,
        "ext_opening_iterations": extended_config.opening_iterations,
        "ext_min_score": extended_config.min_score,
        "ext_max_sources": extended_config.max_sources,
        "match_radius_arcsec": gaia_config.match_radius_arcsec,
        "probability_power": gaia_config.probability_power,
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
    config: Annotated[PointDetectionConfigSchema, Depends(point_detection_query)],
    extended_config: Annotated[
        ExtendedDetectionConfigSchema,
        Depends(extended_detection_query),
    ],
    client_id: Annotated[str, Header(alias="X-Client-Id")] = "anonymous",
    hdu: HduIndex = None,
) -> SourceDetectionResponse:
    _log.info(
        "detect_start",
        record_id=str(record_id),
        fwhm=config.fwhm,
        sigma=config.sigma,
        min_snr=config.min_snr,
    )
    start = time.perf_counter()
    result = await service.detect_from_record(
        record_id,
        client_id=client_id,
        hdu_index=hdu,
        config=config,
        extended_config=extended_config,
    )
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
            config=config,
            extended_config=extended_config,
            gaia_config=_GAIA_DEFAULTS,
        ),
    )


@router.get(
    "/{record_id}/sources/bestPreset",
    response_model=SourcePresetResponse,
    operation_id="getBestPreset",
    summary="Recommend detection parameters measured from this image",
)
async def get_best_preset(
    record_id: RecordId,
    service: Annotated[SourceDetectionService, Depends(source_service_dependency)],
    client_id: Annotated[str, Header(alias="X-Client-Id")] = "anonymous",
    hdu: HduIndex = None,
) -> SourcePresetResponse:
    _log.info("best_preset_start", record_id=str(record_id), client_id=client_id)
    return await service.recommend_preset(
        record_id,
        client_id=client_id,
        hdu_index=hdu,
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
    config: Annotated[PointDetectionConfigSchema, Depends(point_detection_query)],
    extended_config: Annotated[
        ExtendedDetectionConfigSchema,
        Depends(extended_detection_query),
    ],
    gaia_config: Annotated[GaiaMatchConfigSchema, Depends(gaia_match_query)],
    client_id: Annotated[str, Header(alias="X-Client-Id")] = "anonymous",
    hdu: HduIndex = None,
) -> GaiaVerificationResponse | GaiaJobStatusSchema:
    _log.info(
        "gaia_verify_start",
        record_id=str(record_id),
        match_radius_arcsec=gaia_config.match_radius_arcsec,
        probability_power=gaia_config.probability_power,
    )
    key = gaia_job_key(
        record_id=record_id,
        client_id=client_id,
        hdu_index=hdu,
        config=config,
        extended_config=extended_config,
        gaia_config=gaia_config,
    )
    completed = jobs.get(key)
    if completed is not None:
        _log.info("gaia_verify_cache_hit", record_id=str(record_id))
        return completed
    await service.ensure_record(record_id)
    jobs.start(
        key,
        lambda: background(
            record_id,
            client_id=client_id,
            hdu_index=hdu,
            config=config,
            extended_config=extended_config,
            gaia_config=gaia_config,
        ),
    )
    await jobs.wait(key)
    completed = jobs.get(key)
    if completed is not None:
        return completed
    failure = jobs.get_failure(key)
    if failure is not None:
        raise failure
    raise InternalServerError("Gaia verification did not complete")


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
        return GaiaJobStatusSchema(status="pending", job_id=job_id, record_id=record_id)
    failure = jobs.get_failure(job_id)
    if failure is not None:
        raise failure
    raise NotFoundError(f"Unknown Gaia job: {job_id}")
