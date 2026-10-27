from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Path, UploadFile
from fastapi.responses import Response

from astroimage.config import Settings, get_settings
from astroimage.fits.deps import fits_service_dependency
from astroimage.fits.schema import FitsImportSchema, FitsMetadataSchema, FitsUrlImportRequest
from astroimage.fits.service import FitsService
from astroimage.shared.errors import BadRequestError
from astroimage.shared.query import HduIndex

router = APIRouter(prefix="/fits", tags=["fits"])

FitsUpload = Annotated[UploadFile, File(description="FITS file to inspect")]
RecordId = Annotated[UUID, Path(description="Stored FITS record id")]


def _attachment_name(filename: str) -> str:
    cleaned = filename.replace('"', "").replace("\r", "").replace("\n", "")
    if cleaned.strip() == "":
        return "image.fits"
    return cleaned


@router.post(
    "/metadata",
    response_model=FitsMetadataSchema,
    operation_id="extractFitsMetadata",
)
async def extract_fits_metadata(
    file: FitsUpload,
    service: Annotated[FitsService, Depends(fits_service_dependency)],
    hdu: HduIndex = None,
) -> FitsMetadataSchema:
    payload = await file.read()
    source_name = file.filename or "upload.fits"
    metadata = service.metadata_from_bytes(
        payload,
        source_name=source_name,
        hdu_index=hdu,
    )
    return service.to_schema(metadata)


@router.post(
    "",
    response_model=list[FitsImportSchema],
    operation_id="importFitsFiles",
)
async def import_fits_files(
    service: Annotated[FitsService, Depends(fits_service_dependency)],
    settings: Annotated[Settings, Depends(get_settings)],
    files: Annotated[list[UploadFile], File(description="One or more FITS files")],
    description: Annotated[str | None, Form()] = None,
    display_name: Annotated[str | None, Form()] = None,
) -> list[FitsImportSchema]:
    if not files:
        raise BadRequestError("At least one FITS file is required")
    imported: list[FitsImportSchema] = []
    for upload in files:
        payload = await upload.read()
        source_name = upload.filename or "upload.fits"
        record = await service.import_bytes(
            payload,
            source_name=source_name,
            max_bytes=settings.fits_import_max_bytes,
            description=description,
            display_name=display_name,
        )
        imported.append(FitsImportSchema(record_id=record.id, slug=record.slug))
    return imported


@router.post(
    "/from-url",
    response_model=FitsImportSchema,
    operation_id="importFitsFromUrl",
)
async def import_fits_from_url(
    body: FitsUrlImportRequest,
    service: Annotated[FitsService, Depends(fits_service_dependency)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> FitsImportSchema:
    record = await service.import_from_url(
        body.url,
        max_bytes=settings.fits_import_max_bytes,
        description=body.description,
        display_name=body.display_name,
    )
    return FitsImportSchema(record_id=record.id, slug=record.slug)


@router.get(
    "/{record_id}/file",
    operation_id="downloadFitsFile",
    responses={200: {"content": {"application/fits": {}}}},
)
async def download_fits_file(
    record_id: RecordId,
    service: Annotated[FitsService, Depends(fits_service_dependency)],
) -> Response:
    record = await service.get_record(record_id)
    payload = await service.get_payload(record)
    filename = _attachment_name(record.original_filename)
    return Response(
        content=payload,
        media_type="application/fits",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
