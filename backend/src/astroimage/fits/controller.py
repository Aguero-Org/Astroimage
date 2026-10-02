from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile

from astroimage.fits.deps import fits_service_dependency
from astroimage.fits.schema import FitsMetadataSchema
from astroimage.fits.service import FitsService

router = APIRouter(prefix="/fits", tags=["fits"])

FitsUpload = Annotated[UploadFile, File(description="FITS file to inspect")]
HduIndex = Annotated[
    int,
    Query(ge=0, description="Optional image HDU index; defaults to the primary 2D image HDU"),
]


@router.post(
    "/metadata",
    response_model=FitsMetadataSchema,
    operation_id="extractFitsMetadata",
)
async def extract_fits_metadata(
    file: FitsUpload,
    service: Annotated[FitsService, Depends(fits_service_dependency)],
    hdu: HduIndex = None,  # type: ignore[assignment]  # nullable default, non-nullable query
) -> FitsMetadataSchema:
    payload = await file.read()
    source_name = file.filename or "upload.fits"
    metadata = service.metadata_from_bytes(
        payload,
        source_name=source_name,
        hdu_index=hdu,
    )
    return service.to_schema(metadata)
