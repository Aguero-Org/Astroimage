from __future__ import annotations

from typing import Literal
from uuid import UUID

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


class ExtendedDetectionConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sigma: float = Field(default=3.0, ge=0.5)
    smooth_sigma: float = Field(default=8.0, ge=0.5)
    min_area: int = Field(default=500, ge=1)
    max_area: int = Field(default=0, ge=0)
    bin_factor: int = Field(default=8, ge=1)
    closing_iterations: int = Field(default=2, ge=0)
    opening_iterations: int = Field(default=1, ge=0)
    min_score: float = Field(default=0.20, ge=0.0, le=1.0)
    max_sources: int = Field(default=3, ge=0)


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
    width_pixels: float
    height_pixels: float
    area_pixels: int
    peak: float
    mean: float
    flux: float
    relevance_score: float
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
    gaia_url: str | None = None


class GaiaMatchConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    match_radius_arcsec: float = Field(default=4.0, ge=0.0)
    probability_power: float = Field(default=2.0, ge=0.1)


class GaiaMatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: int
    object_type: Literal["point", "extended"]
    rank: int
    ra_deg: float | None = None
    dec_deg: float | None = None
    gaia_match: bool = False
    gaia_separation_arcsec: float | None = None
    gaia_probability: float = 0.0
    gaia_source_id: str | None = None
    gaia_ra_deg: float | None = None
    gaia_dec_deg: float | None = None
    gaia_gmag: float | None = None


class GaiaTypeSummarySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = 0
    matched: int = 0
    match_rate: float = 0.0
    median_separation_arcsec: float | None = None


class GaiaVerificationSummarySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    point: GaiaTypeSummarySchema = Field(default_factory=GaiaTypeSummarySchema)
    extended: GaiaTypeSummarySchema = Field(default_factory=GaiaTypeSummarySchema)


class GaiaVerificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str | None = None
    match_radius_arcsec: float
    probability_power: float
    wcs_present: bool = False
    queried: bool = False
    error: str | None = None
    summary: GaiaVerificationSummarySchema = Field(default_factory=GaiaVerificationSummarySchema)
    matches: list[GaiaMatchSchema] = Field(default_factory=list)


class GaiaJobStatusSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending"] = "pending"
    job_id: str
    record_id: UUID
