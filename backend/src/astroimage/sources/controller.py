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
from astroimage.sources.detection_query import (
    extended_detection_query,
    point_detection_query,
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
_GAIA_DEFAULTS = GaiaMatchConfigSchema()
_log = structlog.get_logger("astroimage.sources.controller")

RecordId = Annotated[
    UUID,
    Path(description="Stored FITS record id"),
]

GaiaMatchRadiusParam = Annotated[float, Query(ge=0.0, le=3600.0)]
GaiaProbabilityPowerParam = Annotated[float, Query(ge=0.1)]
GaiaJobId = Annotated[
    str,
    Path(min_length=1, description="Submission id returned by the gaia verification endpoint"),
]


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
        if completed.error is None:
            _log.info("gaia_verify_cache_hit", record_id=str(record_id))
            return completed
        jobs.discard(key)
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
