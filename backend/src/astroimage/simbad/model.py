from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimbadObject:
    main_id: str
    ra_deg: float
    dec_deg: float
    separation_arcsec: float | None = None
    otype: str | None = None
    otype_text: str | None = None
    spectral_type: str | None = None
    parallax_mas: float | None = None
    parallax_error_mas: float | None = None
    major_axis_arcmin: float | None = None
    minor_axis_arcmin: float | None = None
    position_angle_deg: float | None = None
    radial_velocity_km_s: float | None = None
    redshift: float | None = None
    reference_count: int | None = None


@dataclass(frozen=True)
class SimbadAlias:
    object_id: str
    name: str


@dataclass(frozen=True)
class SimbadReference:
    object_id: str
    bibcode: str
    year: int | None = None
    title: str | None = None
    doi: str | None = None
    journal: str | None = None
    object_count: int | None = None


@dataclass(frozen=True)
class SkyDetection:
    source_id: int
    object_type: str
    ra_deg: float
    dec_deg: float


@dataclass(frozen=True)
class SimbadImageMatch:
    source_id: int
    object_type: str
    separation_arcsec: float
    probability: float
    matched: bool
