from __future__ import annotations

import time
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Path, Query

from astroimage.fits.schema import FitsMetadataSchema
from astroimage.hub.deps import hubble_service_dependency
from astroimage.hub.schema import (
    CandidatePageSchema,
    CandidateSortField,
    CandidateSortOrder,
    ListRecordsResponseSchema,
    RecordSortField,
    SelectCandidateRequestSchema,
    TransferStatusSchema,
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
    cuerpo_celeste: Annotated[
        str | None,
        Query(
            description=(
                "Case-insensitive match on display name, filename, instrument, "
                "proposal id, or MAST data URI"
            ),
        ),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=50)] = 8,
    sort: Annotated[RecordSortField, Query()] = "created_at",
    order: Annotated[CandidateSortOrder, Query()] = "desc",
) -> ListRecordsResponseSchema:
    start = time.perf_counter()
    if cuerpo_celeste:
        _log.info("search_by_name_start", name=cuerpo_celeste, page=page, sort=sort)
        result = await service.search_records(
            cuerpo_celeste,
            page=page,
            limit=limit,
            sort=sort,
            order=order,
        )
        _log.info(
            "search_by_name_complete",
            name=cuerpo_celeste,
            count=len(result.records),
            elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
        )
    else:
        _log.info("list_start", page=page, sort=sort)
        result = await service.list_records(page=page, limit=limit, sort=sort, order=order)
        _log.info(
            "list_complete",
            count=len(result.records),
            elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
        )
    return result


@router.get(
    "/image/search",
    response_model=CandidatePageSchema,
    operation_id="searchHubbleCandidates",
)
async def search_astro_image(
    query: Annotated[str, Query(min_length=1, description="Celestial body to search in Hubble")],
    service: Annotated[HubbleImageService, Depends(hubble_service_dependency)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    min_size_mb: Annotated[float | None, Query(ge=0)] = None,
    sort: Annotated[CandidateSortField, Query()] = "product_filename",
    order: Annotated[CandidateSortOrder, Query()] = "asc",
) -> CandidatePageSchema:
    _log.info("candidate_search_start", target=query, page=page, sort=sort, order=order)
    return await service.search_candidates(
        query,
        page=page,
        limit=limit,
        min_size_mb=min_size_mb,
        sort=sort,
        order=order,
    )


@router.post(
    "/image/search/select",
    response_model=TransferStatusSchema,
    operation_id="selectHubbleCandidate",
)
async def select_astro_image(
    body: SelectCandidateRequestSchema,
    service: Annotated[HubbleImageService, Depends(hubble_service_dependency)],
) -> TransferStatusSchema:
    return await service.select_candidate(body.candidate_token, body.display_name)


@router.get(
    "/image/transfers/{transfer_id}",
    response_model=TransferStatusSchema,
    operation_id="getImageTransfer",
)
async def get_image_transfer(
    transfer_id: RecordId,
    service: Annotated[HubbleImageService, Depends(hubble_service_dependency)],
) -> TransferStatusSchema:
    return await service.get_transfer(transfer_id)


@router.post(
    "/image/transfers/{transfer_id}/cancel",
    response_model=TransferStatusSchema,
    operation_id="cancelImageTransfer",
)
async def cancel_image_transfer(
    transfer_id: RecordId,
    service: Annotated[HubbleImageService, Depends(hubble_service_dependency)],
) -> TransferStatusSchema:
    return await service.cancel(transfer_id)


@router.post(
    "/image/transfers/{transfer_id}/resume",
    response_model=TransferStatusSchema,
    operation_id="resumeImageTransfer",
)
async def resume_image_transfer(
    transfer_id: RecordId,
    service: Annotated[HubbleImageService, Depends(hubble_service_dependency)],
) -> TransferStatusSchema:
    return await service.resume(transfer_id)


@router.delete(
    "/image/{record_id}",
    status_code=204,
    operation_id="deleteHubbleImage",
)
async def delete_astro_image(
    record_id: RecordId,
    service: Annotated[HubbleImageService, Depends(hubble_service_dependency)],
) -> None:
    await service.delete_record(record_id)


@router.get(
    "/image/{record_id}/info",
    response_model=FitsMetadataSchema,
    operation_id="getImageInfo",
)
async def get_image_info(
    record_id: RecordId,
    service: Annotated[HubbleImageService, Depends(hubble_service_dependency)],
) -> FitsMetadataSchema:
    return await service.get_record_info(record_id)
