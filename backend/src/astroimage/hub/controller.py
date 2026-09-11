from __future__ import annotations

import time
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from astroimage.fits.schema import FitsMetadataSchema
from astroimage.hub.deps import hubble_service_dependency
from astroimage.hub.importer import HubbleDownloadError, HubbleNotFoundError
from astroimage.hub.schema import (
    FetchImageResponseSchema,
    ListRecordsResponseSchema,
)
from astroimage.hub.service import HubbleImageService

router = APIRouter(tags=["hub"])
_log = structlog.get_logger("astroimage.hub.controller")

RecordId = Annotated[UUID, Path(description="Stored FITS record id")]


@router.get(
    "/image",
    response_model=ListRecordsResponseSchema,
    operation_id="listHubbleImages",
)
async def list_astro_images(
    service: Annotated[HubbleImageService, Depends(hubble_service_dependency)],
    cuerpo_celeste: Annotated[str | None, Query()] = None,
) -> ListRecordsResponseSchema:
    start = time.perf_counter()
    if cuerpo_celeste:
        _log.info("search_by_name_start", name=cuerpo_celeste)
        result = await service.search_records(cuerpo_celeste)
        _log.info(
            "search_by_name_complete",
            name=cuerpo_celeste,
            count=len(result.records),
            elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
        )
    else:
        _log.info("list_start")
        result = await service.list_records()
        _log.info(
            "list_complete",
            count=len(result.records),
            elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
        )
    return result


@router.get(
    "/image/search",
    response_model=FetchImageResponseSchema,
    operation_id="fetchHubbleImage",
)
async def search_astro_image(
    query: Annotated[str, Query(min_length=1, description="Celestial body to fetch from Hubble")],
    service: Annotated[HubbleImageService, Depends(hubble_service_dependency)],
) -> FetchImageResponseSchema:
    _log.info("fetch_start", target=query)
    start = time.perf_counter()
    try:
        result = await service.fetch(query)
    except HubbleNotFoundError as exc:
        _log.warning("fetch_not_found", target=query, detail=str(exc))
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (HubbleDownloadError, OSError) as exc:
        _log.error("fetch_download_error", target=query, detail=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        _log.warning("fetch_validation_error", target=query, detail=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    _log.info(
        "fetch_complete",
        target=query,
        record_id=str(result.record_id),
        elapsed_ms=elapsed_ms,
    )
    return result


@router.get(
    "/image/{record_id}/info",
    response_model=FitsMetadataSchema,
    operation_id="getImageInfo",
)
async def get_image_info(
    record_id: RecordId,
    service: Annotated[HubbleImageService, Depends(hubble_service_dependency)],
) -> FitsMetadataSchema:
    try:
        return await service.get_record_info(record_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
