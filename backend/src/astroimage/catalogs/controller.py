from __future__ import annotations

import time
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, Path, Query

from astroimage.catalogs.cache import recommendation_cache_key
from astroimage.catalogs.deps import (
    catalog_background_dependency,
    catalog_job_registry_dependency,
    catalog_recommendation_service_dependency,
)
from astroimage.catalogs.jobs import CatalogBackgroundRecommend, CatalogJobRegistry
from astroimage.catalogs.schema import (
    CatalogJobStatusSchema,
    CatalogRecommendationConfigSchema,
    CatalogRecommendationResponse,
)
from astroimage.catalogs.service import CatalogRecommendationService
from astroimage.shared.errors import InternalServerError, NotFoundError

router = APIRouter(prefix="/image", tags=["catalogs"])
_DEFAULTS = CatalogRecommendationConfigSchema()
_log = structlog.get_logger("astroimage.catalogs.controller")

RecordId = Annotated[
    UUID,
    Path(description="Stored FITS record id"),
]
HduIndex = Annotated[
    int,
    Query(ge=0, description="Optional image HDU index; defaults to the first 2D image HDU"),
]
SearchRadiusParam = Annotated[float, Query(ge=0.0, description="VizieR cone radius in arcsec")]
MaxCataloguesParam = Annotated[int, Query(ge=1, description="Cap on catalogues evaluated")]
RowLimitParam = Annotated[
    int, Query(ge=1, description="Row cap requested from VizieR per catalogue")
]
CrossmatchTopParam = Annotated[
    int, Query(ge=0, description="How many top catalogues to crossmatch")
]
CrossmatchRadiusParam = Annotated[float, Query(ge=0.0, description="Crossmatch radius in arcsec")]
CatalogJobId = Annotated[
    str,
    Path(min_length=1, description="Job id returned by the recommendation endpoint"),
]


def _config(
    identifiers: list[str] | None,
    search_radius_arcsec: float,
    max_catalogues: int,
    include_papers: bool,
    row_limit: int,
    crossmatch: bool,
    crossmatch_top: int,
    crossmatch_radius_arcsec: float,
) -> CatalogRecommendationConfigSchema:
    return CatalogRecommendationConfigSchema(
        identifiers=identifiers or [],
        search_radius_arcsec=search_radius_arcsec,
        max_catalogues=max_catalogues,
        include_papers=include_papers,
        row_limit=row_limit,
        crossmatch=crossmatch,
        crossmatch_top=crossmatch_top,
        crossmatch_radius_arcsec=crossmatch_radius_arcsec,
    )


@router.get(
    "/{record_id}/catalogs/recommendations",
    response_model=CatalogRecommendationResponse | CatalogJobStatusSchema,
    operation_id="recommendCatalogs",
    summary="Rank VizieR catalogues and papers relevant to this image",
)
async def recommend_catalogs(
    record_id: RecordId,
    service: Annotated[
        CatalogRecommendationService,
        Depends(catalog_recommendation_service_dependency),
    ],
    background: Annotated[CatalogBackgroundRecommend, Depends(catalog_background_dependency)],
    jobs: Annotated[CatalogJobRegistry, Depends(catalog_job_registry_dependency)],
    client_id: Annotated[str, Header(alias="X-Client-Id")] = "anonymous",
    hdu: HduIndex = None,  # type: ignore[assignment]  # nullable default, non-nullable query
    identifiers: Annotated[list[str] | None, Query(description="Known object identifiers")] = None,
    search_radius_arcsec: SearchRadiusParam = _DEFAULTS.search_radius_arcsec,
    max_catalogues: MaxCataloguesParam = _DEFAULTS.max_catalogues,
    include_papers: bool = _DEFAULTS.include_papers,
    row_limit: RowLimitParam = _DEFAULTS.row_limit,
    crossmatch: bool = _DEFAULTS.crossmatch,
    crossmatch_top: CrossmatchTopParam = _DEFAULTS.crossmatch_top,
    crossmatch_radius_arcsec: CrossmatchRadiusParam = _DEFAULTS.crossmatch_radius_arcsec,
) -> CatalogRecommendationResponse | CatalogJobStatusSchema:
    config = _config(
        identifiers,
        search_radius_arcsec,
        max_catalogues,
        include_papers,
        row_limit,
        crossmatch,
        crossmatch_top,
        crossmatch_radius_arcsec,
    )
    key = recommendation_cache_key(
        record_id=record_id,
        client_id=client_id,
        hdu_index=hdu,
        config=config,
    )
    _log.info(
        "catalog_recommend_start",
        record_id=str(record_id),
        client_id=client_id,
        identifiers=len(config.identifiers),
        radius_arcsec=config.search_radius_arcsec,
    )
    completed = jobs.get(key)
    if completed is not None:
        return completed
    await service.ensure_record(record_id)
    start = time.perf_counter()
    jobs.start(
        key,
        lambda: background(
            record_id,
            client_id=client_id,
            hdu_index=hdu,
            config=config,
        ),
    )
    await jobs.wait(key)
    completed = jobs.get(key)
    if completed is not None:
        _log.info(
            "catalog_recommend_complete",
            record_id=str(record_id),
            catalogue_count=len(completed.recommendations),
            elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
        )
        return completed
    failure = jobs.get_failure(key)
    if failure is not None:
        raise failure
    raise InternalServerError("Catalog recommendation did not complete")


@router.get(
    "/{record_id}/catalogs/recommendations/jobs/{job_id}",
    response_model=CatalogRecommendationResponse | CatalogJobStatusSchema,
    operation_id="getCatalogsJob",
)
async def get_catalogs_job(
    record_id: RecordId,
    job_id: CatalogJobId,
    jobs: Annotated[CatalogJobRegistry, Depends(catalog_job_registry_dependency)],
) -> CatalogRecommendationResponse | CatalogJobStatusSchema:
    completed = jobs.get(job_id)
    if completed is not None:
        return completed
    if jobs.is_running(job_id):
        return CatalogJobStatusSchema(job_id=job_id, record_id=record_id)
    failure = jobs.get_failure(job_id)
    if failure is not None:
        raise failure
    raise NotFoundError(f"Unknown catalog job: {job_id}")
