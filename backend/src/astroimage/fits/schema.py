from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FitsTableInfoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    name: str
    rows: int
    columns: list[str]


class FitsMetadataSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str | None = None
    hdu_index: int
    shape: list[int] | None = None
    telescope: str | None = None
    instrument: str | None = None
    detector: str | None = None
    filter_name: str | None = None
    exptime: float | None = None
    date_obs: str | None = None
    time_obs: str | None = None
    photflam: float | None = None
    photplam: float | None = None
    photbw: float | None = None
    naxis: int | None = None
    naxis1: int | None = None
    naxis2: int | None = None
    crval1: float | None = None
    crval2: float | None = None
    crpix1: float | None = None
    crpix2: float | None = None
    ctype1: str | None = None
    ctype2: str | None = None
    cd1_1: float | None = None
    cd1_2: float | None = None
    cd2_1: float | None = None
    cd2_2: float | None = None
    cdelt1: float | None = None
    cdelt2: float | None = None
    image_hdus: list[int] = Field(default_factory=list)
    tables: list[FitsTableInfoSchema] = Field(default_factory=list)
    header: dict[str, Any] = Field(default_factory=dict)
