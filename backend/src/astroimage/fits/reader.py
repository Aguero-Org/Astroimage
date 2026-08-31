from __future__ import annotations

import io
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _none_if_blank(value: object) -> object | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return value


def _optional_float(value: object) -> float | None:
    value = _none_if_blank(value)
    if value is None:
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _optional_str(value: object) -> str | None:
    value = _none_if_blank(value)
    if value is None:
        return None
    return str(value)


OptStr = Annotated[str | None, BeforeValidator(_optional_str)]
OptFloat = Annotated[float | None, BeforeValidator(_optional_float)]


class FitsImageInfo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    shape: list[int] | None = None
    unit: OptStr = None
    datamin: OptFloat = None
    datamax: OptFloat = None
    datamean: OptFloat = None
    median: OptFloat = None
    background: OptFloat = None


class FitsInstrumentInfo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    telescope: OptStr = None
    instrument: OptStr = None
    detector: OptStr = None
    filter_name: OptStr = None
    exptime: OptFloat = None
    date_obs: OptStr = None
    time_obs: OptStr = None


class FitsPhotometryInfo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    photflam: OptFloat = None
    photplam: OptFloat = None
    photbw: OptFloat = None


class FitsWcsInfo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    present: bool = False
    naxis: int | None = None
    crval: list[float] | None = None
    crpix: list[float] | None = None
    ctype: list[str] | None = None
    cunit: list[str] | None = None
    cd: list[list[float]] | None = None
    cdelt: list[float] | None = None


class FitsHduInfo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    selected: int
    image_indices: list[int] = Field(default_factory=list)


class FitsTableInfo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int
    name: str
    rows: int
    columns: list[str]


class FitsMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_name: OptStr = None
    image: FitsImageInfo = Field(default_factory=FitsImageInfo)
    instrument: FitsInstrumentInfo = Field(default_factory=FitsInstrumentInfo)
    photometry: FitsPhotometryInfo = Field(default_factory=FitsPhotometryInfo)
    wcs: FitsWcsInfo = Field(default_factory=FitsWcsInfo)
    hdus: FitsHduInfo
    tables: list[FitsTableInfo] = Field(default_factory=list)
    header: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class FitsImageData:
    data: np.ndarray
    hdu_index: int
    source_name: str | None = None


_FILTER_KEYS = ("FILTER", "FILTER1", "FILTER2")
_SKIP_CARDS = frozenset({"", "COMMENT", "HISTORY"})
_WCS_HINTS = frozenset(
    {
        "CRVAL1",
        "CRVAL2",
        "CRPIX1",
        "CRPIX2",
        "CTYPE1",
        "CTYPE2",
        "CD1_1",
        "CD1_2",
        "CD2_1",
        "CD2_2",
        "CDELT1",
        "CDELT2",
    }
)


def _card_value(value: object) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def _header_dict(header: fits.Header) -> dict[str, Any]:
    return {key: _card_value(header[key]) for key in header if key not in _SKIP_CARDS}


def _filter_name(header: fits.Header) -> str | None:
    for key in _FILTER_KEYS:
        if key in header:
            return str(header[key])
    return None


def _float_list(values: Any) -> list[float]:
    return [float(value) for value in values]


def _str_list(values: Any) -> list[str]:
    return [str(value).strip() for value in values]


def _wcs_info(header: fits.Header) -> FitsWcsInfo:
    if not _WCS_HINTS.intersection(header.keys()):
        return FitsWcsInfo(present=False)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FITSFixedWarning)
        wcs = WCS(header, naxis=2, relax=True)

    payload: dict[str, Any] = {
        "present": True,
        "naxis": int(wcs.naxis),
        "crval": _float_list(wcs.wcs.crval),
        "crpix": _float_list(wcs.wcs.crpix),
        "ctype": _str_list(wcs.wcs.ctype),
        "cunit": _str_list(wcs.wcs.cunit),
    }
    if wcs.wcs.has_cd():
        payload["cd"] = np.asarray(wcs.wcs.cd, dtype=float).tolist()
        payload["cdelt"] = None
    else:
        payload["cd"] = None
        payload["cdelt"] = _float_list(wcs.wcs.cdelt)
    return FitsWcsInfo.model_validate(payload)


def _image_info(header: fits.Header, data: np.ndarray) -> FitsImageInfo:
    return FitsImageInfo.model_validate(
        {
            "shape": [int(axis_size) for axis_size in data.shape],
            "unit": header.get("BUNIT"),
            "datamin": header.get("DATAMIN"),
            "datamax": header.get("DATAMAX"),
            "datamean": header.get("DATAMEAN"),
            "median": header.get("MEDIAN"),
            "background": header.get("BACKGRND"),
        }
    )


def _instrument_info(header: fits.Header) -> FitsInstrumentInfo:
    return FitsInstrumentInfo.model_validate(
        {
            "telescope": header.get("TELESCOP"),
            "instrument": header.get("INSTRUME"),
            "detector": header.get("DETECTOR"),
            "filter_name": _filter_name(header),
            "exptime": header.get("EXPTIME"),
            "date_obs": header.get("DATE-OBS"),
            "time_obs": header.get("TIME-OBS"),
        }
    )


def _photometry_info(header: fits.Header) -> FitsPhotometryInfo:
    return FitsPhotometryInfo.model_validate(
        {
            "photflam": header.get("PHOTFLAM"),
            "photplam": header.get("PHOTPLAM"),
            "photbw": header.get("PHOTBW"),
        }
    )


def _image_hdus(hdul: fits.HDUList) -> list[int]:
    return [
        index
        for index, hdu in enumerate(hdul)
        if getattr(hdu, "is_image", False)
        and isinstance(hdu.data, np.ndarray)
        and hdu.data.ndim == 2
        and np.issubdtype(hdu.data.dtype, np.number)
    ]


def _choose_hdu(image_hdus: list[int], requested: int | None) -> int:
    if not image_hdus:
        raise ValueError("No 2D numeric image HDU found in FITS file")
    if requested is None:
        return 0 if 0 in image_hdus else image_hdus[0]
    if requested not in image_hdus:
        raise ValueError(f"HDU {requested} is not a 2D image; available: {image_hdus}")
    return requested


def _tables(hdul: fits.HDUList) -> list[FitsTableInfo]:
    return [
        FitsTableInfo(
            index=index,
            name=str(hdu.name or ""),
            rows=len(hdu.data),
            columns=list(hdu.columns.names or ()),
        )
        for index, hdu in enumerate(hdul)
        if isinstance(hdu, (fits.BinTableHDU | fits.TableHDU)) and hdu.data is not None
    ]


def _read(hdul: fits.HDUList, *, source_name: str | None, hdu_index: int | None) -> FitsMetadata:
    image_indices = _image_hdus(hdul)
    selected = _choose_hdu(image_indices, hdu_index)
    hdu = hdul[selected]
    if hdu.data is None:
        raise ValueError(f"HDU {selected} has no data")

    header = hdu.header
    data = np.asarray(hdu.data)
    return FitsMetadata(
        source_name=source_name,
        image=_image_info(header, data),
        instrument=_instrument_info(header),
        photometry=_photometry_info(header),
        wcs=_wcs_info(header),
        hdus=FitsHduInfo(selected=selected, image_indices=image_indices),
        tables=_tables(hdul),
        header=_header_dict(header),
    )


def _read_image_data(
    hdul: fits.HDUList,
    *,
    source_name: str | None,
    hdu_index: int | None,
) -> FitsImageData:
    selected = _choose_hdu(_image_hdus(hdul), hdu_index)
    hdu = hdul[selected]
    if hdu.data is None:
        raise ValueError(f"HDU {selected} has no data")
    return FitsImageData(
        data=np.asarray(hdu.data, dtype=float),
        hdu_index=selected,
        source_name=source_name,
    )


class FitsReader:
    def read_metadata_from_path(
        self,
        path: Path | str,
        *,
        hdu_index: int | None = None,
    ) -> FitsMetadata:
        fits_path = Path(path)
        if not fits_path.is_file():
            raise FileNotFoundError(f"FITS file not found: {fits_path}")
        with fits.open(fits_path) as hdul:
            return _read(hdul, source_name=fits_path.name, hdu_index=hdu_index)

    def read_metadata_from_bytes(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
    ) -> FitsMetadata:
        with fits.open(io.BytesIO(payload)) as hdul:
            return _read(hdul, source_name=source_name, hdu_index=hdu_index)

    def read_image_data_from_path(
        self,
        path: Path | str,
        *,
        hdu_index: int | None = None,
    ) -> FitsImageData:
        fits_path = Path(path)
        if not fits_path.is_file():
            raise FileNotFoundError(f"FITS file not found: {fits_path}")
        with fits.open(fits_path) as hdul:
            return _read_image_data(hdul, source_name=fits_path.name, hdu_index=hdu_index)

    def read_image_data_from_bytes(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
    ) -> FitsImageData:
        if not payload:
            raise ValueError("Empty FITS payload")
        with fits.open(io.BytesIO(payload)) as hdul:
            return _read_image_data(hdul, source_name=source_name, hdu_index=hdu_index)
