from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SimbadImageMatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: int
    object_type: str
    separation_arcsec: float
    probability: float = 0.0
    matched: bool = False


class SimbadReferenceSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bibcode: str
    year: int | None = None
    title: str | None = None
    doi: str | None = None
    journal: str | None = None
    object_count: int | None = None
    ads_url: str | None = None
    doi_url: str | None = None


class SimbadObjectSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    main_id: str
    otype: str | None = None
    otype_text: str | None = None
    ra_deg: float
    dec_deg: float
    separation_arcsec: float | None = None
    spectral_type: str | None = None
    parallax_mas: float | None = None
    parallax_error_mas: float | None = None
    major_axis_arcmin: float | None = None
    minor_axis_arcmin: float | None = None
    position_angle_deg: float | None = None
    radial_velocity_km_s: float | None = None
    redshift: float | None = None
    total_reference_count: int | None = None
    gaia_source_id: str | None = None
    aliases: list[str] = Field(default_factory=list)
    references: list[SimbadReferenceSchema] = Field(default_factory=list)
    image_match: SimbadImageMatchSchema | None = None


class SimbadReferencesConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=25, ge=1, le=200)
    object_type: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z0-9_+.\-]{1,32}$",
    )
    include_aliases: bool = True
    include_bibliography: bool = True
    max_references_per_object: int = Field(default=10, ge=0, le=100)
    crossmatch_radius_arcsec: float = Field(default=3.0, ge=0.0, le=3600.0)
    probability_power: float = Field(default=2.0, ge=0.1)


class SimbadReferencesSummarySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_count: int = 0
    matched_source_count: int = 0
    detection_count: int = 0
    reference_count: int = 0


class SimbadReferencesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str | None = None
    ra_deg: float | None = None
    dec_deg: float | None = None
    radius_arcsec: float = 0.0
    limit: int = 25
    include_aliases: bool = True
    include_bibliography: bool = True
    wcs_present: bool = False
    queried: bool = False
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    summary: SimbadReferencesSummarySchema = Field(default_factory=SimbadReferencesSummarySchema)
    objects: list[SimbadObjectSchema] = Field(default_factory=list)
