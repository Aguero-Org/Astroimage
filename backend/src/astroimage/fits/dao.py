from __future__ import annotations

import io
from pathlib import Path
from typing import Any, BinaryIO

import numpy as np
from astropy.io import fits

from astroimage.fits.model import FitsMetadata, FitsTableInfo

_FILTER_KEYS = ("FILTER", "FILTER1", "FILTER2")


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _as_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _header_card_value(value: object) -> str | int | float | bool | None:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not np.isfinite(number):
            return str(value)
        return number
    if isinstance(value, str):
        return value
    return str(value)


def _serialize_header(header: fits.Header) -> dict[str, Any]:
    cards: dict[str, Any] = {}
    for key in header:
        if not key or key == "HISTORY" or key == "COMMENT":
            continue
        cards[key] = _header_card_value(header.get(key))
    return cards


def _filter_name(header: fits.Header) -> str | None:
    for key in _FILTER_KEYS:
        if key in header:
            value = _as_str(header.get(key))
            if value is not None:
                return value
    return None


def _list_image_hdus(hdul: fits.HDUList) -> list[int]:
    image_hdus: list[int] = []
    for index, hdu in enumerate(hdul):
        data = hdu.data
        if isinstance(data, np.ndarray) and data.ndim == 2 and np.issubdtype(data.dtype, np.number):
            image_hdus.append(index)
    return image_hdus


def _select_image_hdu(hdul: fits.HDUList, requested_hdu: int | None) -> int:
    image_hdus = _list_image_hdus(hdul)
    if not image_hdus:
        msg = "No 2D numeric image HDU found in FITS file"
        raise ValueError(msg)
    if requested_hdu is not None:
        if requested_hdu not in image_hdus:
            msg = f"HDU {requested_hdu} is not a 2D image; available: {image_hdus}"
            raise ValueError(msg)
        return requested_hdu
    if 0 in image_hdus:
        return 0
    return image_hdus[0]


def _list_tables(hdul: fits.HDUList) -> tuple[FitsTableInfo, ...]:
    tables: list[FitsTableInfo] = []
    for index, hdu in enumerate(hdul):
        if not isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
            continue
        if hdu.data is None:
            continue
        columns = tuple(hdu.columns.names or [])
        tables.append(
            FitsTableInfo(
                index=index,
                name=str(hdu.name or ""),
                rows=len(hdu.data),
                columns=columns,
            )
        )
    return tuple(tables)


def _metadata_from_hdul(
    hdul: fits.HDUList,
    *,
    source_name: str | None,
    hdu_index: int | None,
) -> FitsMetadata:
    image_hdus = tuple(_list_image_hdus(hdul))
    selected = _select_image_hdu(hdul, hdu_index)
    hdu = hdul[selected]
    if hdu.data is None:
        msg = f"HDU {selected} has no data"
        raise ValueError(msg)

    data = np.asarray(hdu.data)
    header = hdu.header
    shape = tuple(int(dim) for dim in data.shape) if data.ndim >= 1 else None

    return FitsMetadata(
        source_name=source_name,
        hdu_index=selected,
        shape=shape,
        telescope=_as_str(header.get("TELESCOP")),
        instrument=_as_str(header.get("INSTRUME")),
        detector=_as_str(header.get("DETECTOR")),
        filter_name=_filter_name(header),
        exptime=_as_float(header.get("EXPTIME")),
        date_obs=_as_str(header.get("DATE-OBS")),
        time_obs=_as_str(header.get("TIME-OBS")),
        photflam=_as_float(header.get("PHOTFLAM")),
        photplam=_as_float(header.get("PHOTPLAM")),
        photbw=_as_float(header.get("PHOTBW")),
        naxis=_as_int(header.get("NAXIS")),
        naxis1=_as_int(header.get("NAXIS1")),
        naxis2=_as_int(header.get("NAXIS2")),
        crval1=_as_float(header.get("CRVAL1")),
        crval2=_as_float(header.get("CRVAL2")),
        crpix1=_as_float(header.get("CRPIX1")),
        crpix2=_as_float(header.get("CRPIX2")),
        ctype1=_as_str(header.get("CTYPE1")),
        ctype2=_as_str(header.get("CTYPE2")),
        cd1_1=_as_float(header.get("CD1_1")),
        cd1_2=_as_float(header.get("CD1_2")),
        cd2_1=_as_float(header.get("CD2_1")),
        cd2_2=_as_float(header.get("CD2_2")),
        cdelt1=_as_float(header.get("CDELT1")),
        cdelt2=_as_float(header.get("CDELT2")),
        image_hdus=image_hdus,
        tables=_list_tables(hdul),
        header=_serialize_header(header),
    )


class FitsDao:
    def read_metadata_from_path(
        self,
        path: Path | str,
        *,
        hdu_index: int | None = None,
    ) -> FitsMetadata:
        fits_path = Path(path)
        if not fits_path.is_file():
            msg = f"FITS file not found: {fits_path}"
            raise FileNotFoundError(msg)
        with fits.open(fits_path) as hdul:
            return _metadata_from_hdul(
                hdul,
                source_name=fits_path.name,
                hdu_index=hdu_index,
            )

    def read_metadata_from_bytes(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
    ) -> FitsMetadata:
        buffer: BinaryIO = io.BytesIO(payload)
        with fits.open(buffer) as hdul:
            return _metadata_from_hdul(
                hdul,
                source_name=source_name,
                hdu_index=hdu_index,
            )
