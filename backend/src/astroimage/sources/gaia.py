from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import astropy.units as u
import numpy as np
import structlog
from astropy.coordinates import Angle, SkyCoord
from astroquery.gaia import Gaia

_log = structlog.get_logger("astroimage.sources.gaia")

_GAIA_COLUMNS = ("source_id", "ra", "dec", "phot_g_mean_mag")
_MIN_CONES_RADIUS_ARCSEC = 60.0

Gaia.ROW_LIMIT = -1


@dataclass(frozen=True)
class GaiaObject:
    source_id: str
    ra_deg: float
    dec_deg: float
    gmag: float | None = None


@dataclass(frozen=True)
class GaiaSourceMatch:
    separation_arcsec: float | None
    probability: float
    matched: bool
    gaia_source_id: str | None
    gaia_ra_deg: float | None
    gaia_dec_deg: float | None
    gaia_gmag: float | None


class GaiaCatalogProvider(Protocol):
    def search_cone(self, center: SkyCoord, radius_arcsec: float) -> list[GaiaObject]: ...


class AstroqueryGaiaProvider:
    def search_cone(self, center: SkyCoord, radius_arcsec: float) -> list[GaiaObject]:
        _log.info(
            "gaia_cone_search",
            center_ra=float(center.ra.deg),
            center_dec=float(center.dec.deg),
            radius_arcsec=radius_arcsec,
        )
        radius = Angle(radius_arcsec * u.arcsec)
        job = Gaia.cone_search_async(center, radius=radius, columns=_GAIA_COLUMNS)
        table = job.get_results()
        if table is None or len(table) == 0:
            return []
        wanted = [column for column in _GAIA_COLUMNS if column in table.colnames]
        objects: list[GaiaObject] = []
        for row in table[wanted]:
            objects.append(
                GaiaObject(
                    source_id=str(row["source_id"]),
                    ra_deg=float(row["ra"]),
                    dec_deg=float(row["dec"]),
                    gmag=_optional_gmag(row["phot_g_mean_mag"]),
                )
            )
        return objects


def match_sources_to_gaia(
    detected_coords: list[SkyCoord],
    gaia_objects: list[GaiaObject],
    *,
    match_radius_arcsec: float,
    probability_power: float,
) -> list[GaiaSourceMatch]:
    if not detected_coords:
        return []
    radius = max(float(match_radius_arcsec), 1e-9)
    power = max(float(probability_power), 0.1)
    empty_match = GaiaSourceMatch(
        separation_arcsec=None,
        probability=0.0,
        matched=False,
        gaia_source_id=None,
        gaia_ra_deg=None,
        gaia_dec_deg=None,
        gaia_gmag=None,
    )
    if not gaia_objects:
        return [empty_match for _ in detected_coords]
    coords = SkyCoord(detected_coords)
    gaia_coords = SkyCoord(
        ra=[obj.ra_deg for obj in gaia_objects] * u.deg,
        dec=[obj.dec_deg for obj in gaia_objects] * u.deg,
        frame="icrs",
    )
    indexes, separations, _ = coords.match_to_catalog_sky(gaia_coords)
    matches: list[GaiaSourceMatch] = []
    for _, index, separation in zip(coords, indexes, separations, strict=True):
        sep_arcsec = float(separation.to_value(u.arcsec))
        matched = sep_arcsec <= radius
        normalized = min(sep_arcsec / radius, 1.0)
        probability = (1.0 - normalized) ** power if matched else 0.0
        gaia_object = gaia_objects[int(index)]
        matches.append(
            GaiaSourceMatch(
                separation_arcsec=sep_arcsec,
                probability=probability,
                matched=matched,
                gaia_source_id=gaia_object.source_id if matched else None,
                gaia_ra_deg=gaia_object.ra_deg if matched else None,
                gaia_dec_deg=gaia_object.dec_deg if matched else None,
                gaia_gmag=gaia_object.gmag if matched else None,
            )
        )
    return matches


def search_radius_arcsec(
    center: SkyCoord,
    detected_coords: list[SkyCoord],
    *,
    match_radius_arcsec: float,
) -> float:
    max_separation = float(center.separation(SkyCoord(detected_coords)).max().to_value(u.arcsec))
    return max(max_separation + match_radius_arcsec, _MIN_CONES_RADIUS_ARCSEC)


def _optional_gmag(value: object) -> float | None:
    if value is None:
        return None
    try:
        converted = float(str(value))
    except (TypeError, ValueError):
        return None
    if not np.isfinite(converted):
        return None
    return converted
