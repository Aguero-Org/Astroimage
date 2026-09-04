from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PointDetectionConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fwhm: float = Field(default=5.5, ge=0.5)
    sigma: float = Field(default=9.0, ge=1.0)
    min_snr: float = Field(default=6.0, ge=0.0)
    min_score: float = Field(default=0.18, ge=0.0, le=1.0)
    min_distance: float = Field(default=4.0, ge=0.0)
    visual_weight: float = Field(default=0.80, ge=0.0, le=1.0)
    visual_area_radius: float = Field(default=7.0, ge=1.0)
    visual_area_sigma: float = Field(default=2.0, ge=0.0)
    max_sources: int = Field(default=50, ge=0)
    extended_min_snr: float = Field(default=0.0, ge=0.0)
    extended_max_sources: int = Field(default=50, ge=0)


class PointSourceSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: int
    rank: int
    xcentroid: float
    ycentroid: float
    snr: float
    relevance_score: float
    peak: float | None = None
    flux: float | None = None
    object_type: Literal["point"] = "point"


class ExtendedSourceSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: int
    rank: int
    xcentroid: float
    ycentroid: float
    snr: float
    peak: float | None = None
    flux: float | None = None
    object_type: Literal["extended"] = "extended"


class DetectionSummarySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    point_count: int = 0
    extended_count: int = 0


class SourceDetectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str | None = None
    summary: DetectionSummarySchema
    point_sources: list[PointSourceSchema] = Field(default_factory=list)
    extended_sources: list[ExtendedSourceSchema] = Field(default_factory=list)
