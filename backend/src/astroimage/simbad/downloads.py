from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass

from astroimage.catalogs.cone_cache import StoredConeRow, StoredConeTable
from astroimage.catalogs.region import region_key
from astroimage.simbad.model import SimbadObject

SIMBAD_SOURCE = "simbad"
SIMBAD_CATALOGUE_ID = "simbad"
_ANY_OBJECT_TYPE = "*"
_TEXT_FIELDS = ("main_id", "otype", "otype_text", "spectral_type")
_FLOAT_FIELDS = (
    "parallax_mas",
    "parallax_error_mas",
    "major_axis_arcmin",
    "minor_axis_arcmin",
    "position_angle_deg",
    "radial_velocity_km_s",
    "redshift",
)
_INT_FIELDS = ("reference_count",)
_VALUE_FIELDS = (*_TEXT_FIELDS, *_FLOAT_FIELDS, *_INT_FIELDS)


@dataclass(frozen=True)
class SimbadDownloadQuery:
    source: str
    region_key: str
    ra_deg: float
    dec_deg: float
    radius_arcsec: float
    row_limit: int
    region_suffix: str


def simbad_region_key(
    *,
    ra_deg: float,
    dec_deg: float,
    radius_arcsec: float,
    row_limit: int,
    object_type: str | None,
) -> str:
    base = region_key(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        radius_arcsec=radius_arcsec,
        row_limit=row_limit,
    )
    return f"{base}{simbad_region_suffix(object_type)}"


def simbad_region_suffix(object_type: str | None) -> str:
    token = object_type if object_type else _ANY_OBJECT_TYPE
    return f":type={token}"


def simbad_download_query(
    *,
    ra_deg: float,
    dec_deg: float,
    radius_arcsec: float,
    row_limit: int,
    object_type: str | None,
) -> SimbadDownloadQuery:
    return SimbadDownloadQuery(
        source=SIMBAD_SOURCE,
        region_key=simbad_region_key(
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            radius_arcsec=radius_arcsec,
            row_limit=row_limit,
            object_type=object_type,
        ),
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        radius_arcsec=radius_arcsec,
        row_limit=row_limit,
        region_suffix=simbad_region_suffix(object_type),
    )


def table_from_objects(objects: Sequence[SimbadObject]) -> StoredConeTable:
    return StoredConeTable(
        catalogue_id=SIMBAD_CATALOGUE_ID,
        rows=tuple(
            StoredConeRow(
                index=index,
                ra_deg=simbad_object.ra_deg,
                dec_deg=simbad_object.dec_deg,
                separation_arcsec=simbad_object.separation_arcsec,
                values=_pairs(simbad_object),
            )
            for index, simbad_object in enumerate(objects)
        ),
    )


def objects_from_tables(tables: Sequence[StoredConeTable]) -> list[SimbadObject]:
    return [
        restored
        for table in tables
        if table.catalogue_id == SIMBAD_CATALOGUE_ID
        for row in table.rows
        if (restored := _object_from_row(row)) is not None
    ]


def _pairs(simbad_object: SimbadObject) -> tuple[tuple[str, str], ...]:
    return tuple(
        (name, json.dumps(value))
        for name in _VALUE_FIELDS
        if (value := getattr(simbad_object, name)) is not None
    )


def _object_from_row(row: StoredConeRow) -> SimbadObject | None:
    if row.ra_deg is None or row.dec_deg is None:
        return None
    fields = {name: json.loads(raw) for name, raw in row.values}
    main_id = fields.get("main_id")
    if not isinstance(main_id, str):
        return None
    return SimbadObject(
        main_id=main_id,
        ra_deg=row.ra_deg,
        dec_deg=row.dec_deg,
        separation_arcsec=row.separation_arcsec,
        otype=_text(fields, "otype"),
        otype_text=_text(fields, "otype_text"),
        spectral_type=_text(fields, "spectral_type"),
        parallax_mas=_float_value(fields, "parallax_mas"),
        parallax_error_mas=_float_value(fields, "parallax_error_mas"),
        major_axis_arcmin=_float_value(fields, "major_axis_arcmin"),
        minor_axis_arcmin=_float_value(fields, "minor_axis_arcmin"),
        position_angle_deg=_float_value(fields, "position_angle_deg"),
        radial_velocity_km_s=_float_value(fields, "radial_velocity_km_s"),
        redshift=_float_value(fields, "redshift"),
        reference_count=_whole(fields, "reference_count"),
    )


def _text(fields: dict[str, object], name: str) -> str | None:
    value = fields.get(name)
    if isinstance(value, str):
        return value
    return None


def _float_value(fields: dict[str, object], name: str) -> float | None:
    value = fields.get(name)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _whole(fields: dict[str, object], name: str) -> int | None:
    value = fields.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value
