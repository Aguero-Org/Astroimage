from __future__ import annotations

from typing import Annotated, Any

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
