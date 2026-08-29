from __future__ import annotations

from pathlib import Path

from astroimage.fits.dao import FitsDao
from astroimage.fits.model import FitsMetadata
from astroimage.fits.schema import FitsMetadataSchema, FitsTableInfoSchema


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
            msg = "Empty FITS payload"
            raise ValueError(msg)
        return self._dao.read_metadata_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )

    def to_schema(self, metadata: FitsMetadata) -> FitsMetadataSchema:
        return FitsMetadataSchema(
            source_name=metadata.source_name,
            hdu_index=metadata.hdu_index,
            shape=list(metadata.shape) if metadata.shape is not None else None,
            telescope=metadata.telescope,
            instrument=metadata.instrument,
            detector=metadata.detector,
            filter_name=metadata.filter_name,
            exptime=metadata.exptime,
            date_obs=metadata.date_obs,
            time_obs=metadata.time_obs,
            photflam=metadata.photflam,
            photplam=metadata.photplam,
            photbw=metadata.photbw,
            naxis=metadata.naxis,
            naxis1=metadata.naxis1,
            naxis2=metadata.naxis2,
            crval1=metadata.crval1,
            crval2=metadata.crval2,
            crpix1=metadata.crpix1,
            crpix2=metadata.crpix2,
            ctype1=metadata.ctype1,
            ctype2=metadata.ctype2,
            cd1_1=metadata.cd1_1,
            cd1_2=metadata.cd1_2,
            cd2_1=metadata.cd2_1,
            cd2_2=metadata.cd2_2,
            cdelt1=metadata.cdelt1,
            cdelt2=metadata.cdelt2,
            image_hdus=list(metadata.image_hdus),
            tables=[
                FitsTableInfoSchema(
                    index=table.index,
                    name=table.name,
                    rows=table.rows,
                    columns=list(table.columns),
                )
                for table in metadata.tables
            ],
            header=dict(metadata.header),
        )
