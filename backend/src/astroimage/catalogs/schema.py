from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CrossmatchRowSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalogue_row_index: int
    ra_deg: float | None = None
    dec_deg: float | None = None
    object_identifier: str | None = None
    detection_source_id: int | None = None
    object_type: str | None = None
    separation_arcsec: float | None = None
    matched: bool = False
    probability: float = 0.0


class CatalogCrossmatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalogue_id: str
    match_radius_arcsec: float
    detection_count: int = 0
    matched_count: int = 0
    matches: list[CrossmatchRowSchema] = Field(default_factory=list)


class CatalogRecommendationItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int
    catalogue_id: str
    match_type: Literal["OBJECT_IN_TABLE", "CATALOGUE_ONLY"]
    separation_arcsec: float | None = None
    object_found_in_table: bool = False
    object_identifier: str | None = None
    identifier_columns: str | None = None
    spatial_match: bool = False
    identifier_match: bool = False
    spatial_score: float = 0.0
    identifier_score: float = 0.0
    paper_score: float = 0.0
    doi_score: float = 0.0
    total_score: float = 0.0
    catalogue_title: str | None = None
    catalogue_authors: str | None = None
    catalogue_description: str | None = None
    catalogue_keywords: str | None = None
    catalogue_bibcode: str | None = None
    catalogue_doi: str | None = None
    catalogue_doi_url: str | None = None
    paper_bibcode: str | None = None
    paper_doi: str | None = None
    paper_doi_url: str | None = None
    paper_ads_url: str | None = None
    vizier_url: str | None = None
    readme_url: str | None = None
    readme_bibcodes: list[str] = Field(default_factory=list)
    readme_dois: list[str] = Field(default_factory=list)
    crossmatch: CatalogCrossmatchSchema | None = None


class CatalogRecommendationConfigSchema(BaseModel):
    """Parameters that fully determine a recommendation run (cache/job key)."""

    model_config = ConfigDict(extra="forbid")

    identifiers: list[str] = Field(default_factory=list)
    search_radius_arcsec: float = Field(default=10.0, ge=0.0)
    max_catalogues: int = Field(default=100, ge=1)
    include_papers: bool = True
    row_limit: int = Field(default=50, ge=1)
    crossmatch: bool = False
    crossmatch_top: int = Field(default=5, ge=0)
    crossmatch_radius_arcsec: float = Field(default=2.5, ge=0.0)


class CatalogRecommendationSummarySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalogue_count: int = 0
    object_in_table_count: int = 0
    queried_catalogue_count: int = 0


class CatalogRecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str | None = None
    ra_deg: float | None = None
    dec_deg: float | None = None
    radius_arcsec: float = 0.0
    include_papers: bool = True
    wcs_present: bool = False
    queried: bool = False
    error: str | None = None
    summary: CatalogRecommendationSummarySchema = Field(
        default_factory=CatalogRecommendationSummarySchema
    )
    recommendations: list[CatalogRecommendationItemSchema] = Field(default_factory=list)


class CatalogJobStatusSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending"] = "pending"
    job_id: str
    record_id: UUID
