from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from astroimage.fits.schema import FitsMetadataSchema
from astroimage.fits.service import FitsService

router = APIRouter(prefix="/fits", tags=["fits"])
_service = FitsService()

FitsUpload = Annotated[UploadFile, File(description="FITS file to inspect")]
HduIndex = Annotated[
    int | None,
    Query(ge=0, description="Optional image HDU index; defaults to the primary 2D image HDU"),
]


@router.post(
    "/metadata",
    response_model=FitsMetadataSchema,
    operation_id="extractFitsMetadata",
)
async def extract_fits_metadata(
    file: FitsUpload,
    hdu: HduIndex = None,
) -> FitsMetadataSchema:
    payload = await file.read()
    try:
        metadata = _service.metadata_from_bytes(
            payload,
            source_name=file.filename,
            hdu_index=hdu,
        )
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _service.to_schema(metadata)
