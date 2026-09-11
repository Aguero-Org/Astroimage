from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FitsImageInfoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shape: list[int] | None = None
    unit: str | None = None
    datamin: float | None = None
    datamax: float | None = None
    datamean: float | None = None
    median: float | None = None
    background: float | None = None


class FitsInstrumentInfoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    telescope: str | None = None
    instrument: str | None = None
    detector: str | None = None
    filter_name: str | None = None
    exptime: float | None = None
    date_obs: str | None = None
    time_obs: str | None = None


class FitsPhotometryInfoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    photflam: float | None = None
    photplam: float | None = None
    photbw: float | None = None


class FitsWcsInfoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    present: bool = False
    naxis: int | None = None
    crval: list[float] | None = None
    crpix: list[float] | None = None
    ctype: list[str] | None = None
    cunit: list[str] | None = None
    cd: list[list[float]] | None = None
    cdelt: list[float] | None = None


class FitsHduDetailSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    extname: str | None = None
    shape: list[int] | None = None
    kind: str | None = None
    ra: float | None = None
    dec: float | None = None


class FitsHduInfoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected: int
    image_indices: list[int] = Field(default_factory=list)
    images: list[FitsHduDetailSchema] = Field(default_factory=list)


class FitsTableInfoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    name: str
    rows: int
    columns: list[str]


class FitsMetadataSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str | None = None
    image: FitsImageInfoSchema = Field(default_factory=FitsImageInfoSchema)
    instrument: FitsInstrumentInfoSchema = Field(default_factory=FitsInstrumentInfoSchema)
    photometry: FitsPhotometryInfoSchema = Field(default_factory=FitsPhotometryInfoSchema)
    wcs: FitsWcsInfoSchema = Field(default_factory=FitsWcsInfoSchema)
    hdus: FitsHduInfoSchema
    tables: list[FitsTableInfoSchema] = Field(default_factory=list)
    header: dict[str, Any] = Field(default_factory=dict)


class FitsRecordSummarySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: UUID
    name: str
