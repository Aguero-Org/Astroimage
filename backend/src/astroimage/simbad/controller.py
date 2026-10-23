from __future__ import annotations

import time
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, Path, Query

from astroimage.simbad.deps import simbad_reference_service_dependency
from astroimage.simbad.schema import SimbadReferencesConfigSchema, SimbadReferencesResponse
from astroimage.simbad.service import SimbadReferenceService

router = APIRouter(prefix="/image", tags=["simbad"])
_DEFAULTS = SimbadReferencesConfigSchema()
_log = structlog.get_logger("astroimage.simbad.controller")

RecordId = Annotated[
    UUID,
    Path(description="Stored FITS record id"),
]
HduIndex = Annotated[
    int,
    Query(ge=0, description="Optional image HDU index; defaults to the first 2D image HDU"),
]
LimitParam = Annotated[int, Query(ge=1, le=200, description="Maximum SIMBAD objects returned")]
ObjectTypeParam = Annotated[
    str | None,
    Query(
        pattern=r"^[A-Za-z0-9_+.\-]{1,32}$",
        description="SIMBAD object type code, for example SNR or G",
    ),
]
MaxReferencesParam = Annotated[
    int,
    Query(ge=0, le=100, description="Maximum references attached to each object"),
]
CrossmatchRadiusParam = Annotated[
    float,
    Query(ge=0.0, le=3600.0, description="Image source crossmatch radius in arcsec"),
]
ProbabilityPowerParam = Annotated[
    float,
    Query(ge=0.1, description="Crossmatch probability exponent"),
]


@router.get(
    "/{record_id}/simbad-references",
    response_model=SimbadReferencesResponse,
    operation_id="getSimbadReferences",
    summary="List SIMBAD objects, identifiers, and bibliography for this image",
    responses={404: {"description": "FITS record not found"}},
)
async def get_simbad_references(
    record_id: RecordId,
    service: Annotated[SimbadReferenceService, Depends(simbad_reference_service_dependency)],
    client_id: Annotated[str, Header(alias="X-Client-Id")] = "anonymous",
    hdu: HduIndex = None,  # type: ignore[assignment]
    limit: LimitParam = _DEFAULTS.limit,
    object_type: ObjectTypeParam = _DEFAULTS.object_type,
    include_aliases: bool = _DEFAULTS.include_aliases,
    include_bibliography: bool = _DEFAULTS.include_bibliography,
    max_references: MaxReferencesParam = _DEFAULTS.max_references_per_object,
    crossmatch_radius_arcsec: CrossmatchRadiusParam = _DEFAULTS.crossmatch_radius_arcsec,
    probability_power: ProbabilityPowerParam = _DEFAULTS.probability_power,
    refresh: bool = False,
) -> SimbadReferencesResponse:
    config = SimbadReferencesConfigSchema(
        limit=limit,
        object_type=object_type,
        include_aliases=include_aliases,
        include_bibliography=include_bibliography,
        max_references_per_object=max_references,
        crossmatch_radius_arcsec=crossmatch_radius_arcsec,
        probability_power=probability_power,
    )
    _log.info(
        "simbad_references_start",
        record_id=str(record_id),
        client_id=client_id,
        limit=limit,
        object_type=object_type,
        include_aliases=include_aliases,
        include_bibliography=include_bibliography,
    )
    start = time.perf_counter()
    result = await service.references_from_record(
        record_id,
        client_id=client_id,
        hdu_index=hdu,
        config=config,
        refresh=refresh,
    )
    _log.info(
        "simbad_references_complete",
        record_id=str(record_id),
        object_count=len(result.objects),
        reference_count=result.summary.reference_count,
        queried=result.queried,
        elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
    )
    return result
