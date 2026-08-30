from __future__ import annotations

from pathlib import Path

from astroimage.fits.dao import FitsDao
from astroimage.fits.model import FitsImageData, FitsMetadata
from astroimage.fits.schema import FitsMetadataSchema


class FitsService:
    def __init__(self, dao: FitsDao | None = None) -> None:
        self._dao = dao or FitsDao()

    def metadata_from_path(
        self,
        path: Path | str,
        *,
        hdu_index: int | None = None,
    ) -> FitsMetadata:
        return self._dao.read_metadata_from_path(path, hdu_index=hdu_index)

    def metadata_from_bytes(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
    ) -> FitsMetadata:
        if not payload:
            raise ValueError("Empty FITS payload")
        return self._dao.read_metadata_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )

    def image_data_from_path(
        self,
        path: Path | str,
        *,
        hdu_index: int | None = None,
    ) -> FitsImageData:
        return self._dao.read_image_data_from_path(path, hdu_index=hdu_index)

    def image_data_from_bytes(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
    ) -> FitsImageData:
        if not payload:
            raise ValueError("Empty FITS payload")
        return self._dao.read_image_data_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )

    def to_schema(self, metadata: FitsMetadata) -> FitsMetadataSchema:
        return FitsMetadataSchema.model_validate(metadata.model_dump())
