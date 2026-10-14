from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CatalogRow:
    """One row of a VizieR table, reduced to what the ranking needs.

    ``values`` keeps the text of every non-empty column so identifier lookups
    can run after the astropy table has been released.
    """

    index: int
    ra_deg: float | None = None
    dec_deg: float | None = None
    separation_arcsec: float | None = None
    values: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class IdentifierMatch:
    """Identifiers of the searched object found inside a catalogue row."""

    identifiers: tuple[str, ...] = ()
    columns: tuple[str, ...] = ()


@dataclass(frozen=True)
class CatalogTable:
    """A VizieR table returned for a cone search."""

    catalogue_id: str
    column_names: tuple[str, ...] = ()
    rows: tuple[CatalogRow, ...] = ()


@dataclass(frozen=True)
class CatalogMetadata:
    """Catalogue-level metadata advertised by VizieR."""

    catalogue_id: str
    title: str | None = None
    authors: str | None = None
    doi: str | None = None
    webpage: str | None = None
    origin_article: str | None = None


@dataclass(frozen=True)
class CatalogEvaluation:
    """A scored catalogue, mirroring the reference ranking CSV."""

    catalogue_id: str
    metadata: CatalogMetadata
    match_type: str
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
    catalogue_bibcode: str | None = None
    catalogue_doi: str | None = None
    catalogue_doi_url: str | None = None
    paper_bibcode: str | None = None
    paper_doi: str | None = None
    paper_doi_url: str | None = None
    paper_ads_url: str | None = None
    vizier_url: str | None = None
    readme_url: str | None = None
    readme_bibcodes: tuple[str, ...] = ()
    readme_dois: tuple[str, ...] = ()


@dataclass(frozen=True)
class DetectionCoordinate:
    """A detected image source projected to the sky, for crossmatching."""

    source_id: int
    object_type: str
    ra_deg: float
    dec_deg: float


@dataclass(frozen=True)
class CrossmatchRow:
    """One catalogue row matched (or not) against the image detections."""

    catalogue_row_index: int
    ra_deg: float | None = None
    dec_deg: float | None = None
    object_identifier: str | None = None
    detection_source_id: int | None = None
    object_type: str | None = None
    separation_arcsec: float | None = None
    matched: bool = False
    probability: float = 0.0


@dataclass(frozen=True)
class CatalogCrossmatch:
    """Crossmatch of one recommended catalogue against image detections."""

    catalogue_id: str
    match_radius_arcsec: float
    detection_count: int = 0
    matched_count: int = 0
    matches: tuple[CrossmatchRow, ...] = field(default_factory=tuple)
