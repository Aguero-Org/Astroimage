from __future__ import annotations

import astropy.units as u
from astropy.coordinates import SkyCoord

from astroimage.catalogs.model import (
    CatalogCrossmatch,
    CatalogRow,
    CrossmatchRow,
    DetectionCoordinate,
)


def _usable_rows(rows: tuple[CatalogRow, ...]) -> list[tuple[CatalogRow, float, float]]:
    usable: list[tuple[CatalogRow, float, float]] = []
    for row in rows:
        if row.ra_deg is None or row.dec_deg is None:
            continue
        usable.append((row, float(row.ra_deg), float(row.dec_deg)))
    return usable


def _crossmatch_row(
    row: CatalogRow,
    ra_deg: float,
    dec_deg: float,
    detection: DetectionCoordinate,
    separation_arcsec: float,
    *,
    radius: float,
    power: float,
) -> CrossmatchRow:
    matched = separation_arcsec <= radius
    normalized = min(separation_arcsec / radius, 1.0)
    return CrossmatchRow(
        catalogue_row_index=row.index,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        object_identifier=_join_identifiers(row),
        detection_source_id=detection.source_id if matched else None,
        object_type=detection.object_type if matched else None,
        separation_arcsec=separation_arcsec,
        matched=matched,
        probability=(1.0 - normalized) ** power if matched else 0.0,
    )


def crossmatch_catalog(
    catalogue_id: str,
    rows: tuple[CatalogRow, ...],
    detections: list[DetectionCoordinate],
    *,
    match_radius_arcsec: float,
    probability_power: float = 2.0,
) -> CatalogCrossmatch:
    """Match catalogue sky positions against image detections.

    Same geometry and probability shape used by ``sources.gaia`` and the
    reference project: closest neighbour within ``match_radius_arcsec`` wins.
    """
    usable = _usable_rows(rows)
    if not usable or not detections:
        return CatalogCrossmatch(
            catalogue_id=catalogue_id,
            match_radius_arcsec=match_radius_arcsec,
            detection_count=len(detections),
        )

    catalogue_coords = SkyCoord(
        ra=[ra for _, ra, _ in usable] * u.deg,
        dec=[dec for _, _, dec in usable] * u.deg,
        frame="icrs",
    )
    detection_coords = SkyCoord(
        ra=[detection.ra_deg for detection in detections] * u.deg,
        dec=[detection.dec_deg for detection in detections] * u.deg,
        frame="icrs",
    )
    indexes, separations, _ = catalogue_coords.match_to_catalog_sky(detection_coords)
    radius = max(float(match_radius_arcsec), 1e-9)
    power = max(float(probability_power), 0.1)
    matches = tuple(
        _crossmatch_row(
            row,
            ra_deg,
            dec_deg,
            detections[int(index)],
            float(separation.to_value(u.arcsec)),
            radius=radius,
            power=power,
        )
        for (row, ra_deg, dec_deg), index, separation in zip(
            usable, indexes, separations, strict=True
        )
    )
    return CatalogCrossmatch(
        catalogue_id=catalogue_id,
        match_radius_arcsec=match_radius_arcsec,
        detection_count=len(detections),
        matched_count=sum(match.matched for match in matches),
        matches=matches,
    )


def _join_identifiers(row: CatalogRow) -> str | None:
    return next(
        (
            text
            for column, text in row.values
            if column.startswith("_") is False and any(character.isalpha() for character in text)
        ),
        None,
    )
