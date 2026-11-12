from __future__ import annotations

from dataclasses import replace

import astropy.units as u
from astropy.coordinates import SkyCoord

from astroimage.catalogs.model import CatalogRow, CatalogTable


def narrow_to_cone(
    tables: list[CatalogTable],
    center: SkyCoord,
    radius_arcsec: float,
) -> list[CatalogTable]:
    narrowed: list[CatalogTable] = []
    for table in tables:
        rows = _narrow_rows(table.rows, center, radius_arcsec)
        if rows:
            narrowed.append(
                CatalogTable(
                    catalogue_id=table.catalogue_id,
                    column_names=table.column_names,
                    rows=rows,
                )
            )
    return narrowed


def _with_coordinates(row: CatalogRow) -> tuple[CatalogRow, float, float] | None:
    if row.ra_deg is None or row.dec_deg is None:
        return None
    return (row, row.ra_deg, row.dec_deg)


def _separations_arcsec(
    located: list[tuple[CatalogRow, float, float]],
    center: SkyCoord,
) -> dict[int, float]:
    if not located:
        return {}
    coordinates = SkyCoord(
        ra=[ra_deg for _, ra_deg, _ in located] * u.deg,
        dec=[dec_deg for _, _, dec_deg in located] * u.deg,
        frame="icrs",
    )
    values = coordinates.separation(center).to_value(u.arcsec)
    return {
        row.index: float(separation)
        for (row, _, _), separation in zip(located, values, strict=True)
    }


def _row_in_cone(
    row: CatalogRow,
    separations: dict[int, float],
    radius_arcsec: float,
) -> CatalogRow | None:
    separation = separations.get(row.index)
    if separation is None:
        return replace(row, separation_arcsec=None)
    if separation <= radius_arcsec:
        return replace(row, separation_arcsec=separation)
    return None


def _narrow_rows(
    rows: tuple[CatalogRow, ...],
    center: SkyCoord,
    radius_arcsec: float,
) -> tuple[CatalogRow, ...]:
    located = [position for row in rows if (position := _with_coordinates(row)) is not None]
    separations = _separations_arcsec(located, center)
    return tuple(
        kept for row in rows if (kept := _row_in_cone(row, separations, radius_arcsec)) is not None
    )
