from __future__ import annotations

import re
from typing import Any, Protocol

import numpy as np
from astropy.coordinates import SkyCoord
from astroquery.simbad import Simbad

from astroimage.shared.logging import simbad_provider_log as _log
from astroimage.simbad.model import SimbadAlias, SimbadObject, SimbadReference

_OBJECT_TYPE_PATTERN = re.compile(r"^[A-Za-z0-9_+.\-]{1,32}$")


class SimbadQueryError(Exception):
    """SIMBAD did not return a usable result for this query."""


class SimbadCatalogProvider(Protocol):
    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
        object_type: str | None = None,
    ) -> list[SimbadObject]: ...

    def query_aliases(self, main_ids: list[str], *, max_records: int) -> list[SimbadAlias]: ...

    def query_references(
        self,
        main_ids: list[str],
        *,
        max_records: int,
    ) -> list[SimbadReference]: ...


class AstroquerySimbadProvider:
    def __init__(self, *, timeout_s: float = 120.0) -> None:
        self._timeout_s = timeout_s

    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
        object_type: str | None = None,
    ) -> list[SimbadObject]:
        _log.info(
            "simbad_query_region",
            center_ra=float(center.ra.deg),
            center_dec=float(center.dec.deg),
            radius_arcsec=radius_arcsec,
            row_limit=row_limit,
            object_type=object_type,
        )
        radius_deg = max(float(radius_arcsec), 0.0) / 3600.0
        query = f"""
SELECT TOP {int(row_limit)}
       basic.main_id,
       basic.ra,
       basic.dec,
       basic.otype,
       basic.otype_txt,
       basic.sp_type,
       basic.plx_value,
       basic.plx_err,
       basic.galdim_majaxis,
       basic.galdim_minaxis,
       basic.galdim_angle,
       basic.rvz_radvel,
       basic.rvz_redshift,
       basic.rvz_type,
       basic.nbref,
       DISTANCE(
           POINT('ICRS', basic.ra, basic.dec),
           POINT('ICRS', {float(center.ra.deg)}, {float(center.dec.deg)})
       ) AS separation_deg
FROM basic
WHERE CONTAINS(
    POINT('ICRS', basic.ra, basic.dec),
    CIRCLE('ICRS', {float(center.ra.deg)}, {float(center.dec.deg)}, {radius_deg})
) = 1
{_object_type_clause(object_type)}
ORDER BY separation_deg ASC
"""
        table = self._query_tap(query, maxrec=int(row_limit))
        return objects_from_table(table)

    def query_aliases(self, main_ids: list[str], *, max_records: int) -> list[SimbadAlias]:
        if not main_ids or max_records <= 0:
            return []
        query = f"""
SELECT TOP {int(max_records)} basic.main_id, ident.id
FROM basic
JOIN ident ON basic.oid = ident.oidref
WHERE basic.main_id IN ({_quoted_values(main_ids)})
ORDER BY id
"""
        table = self._query_tap(query, maxrec=int(max_records))
        return aliases_from_table(table)

    def query_references(
        self,
        main_ids: list[str],
        *,
        max_records: int,
    ) -> list[SimbadReference]:
        if not main_ids or max_records <= 0:
            return []
        query = f"""
SELECT TOP {int(max_records)}
       basic.main_id,
       ref.bibcode,
       ref."year",
       ref.title,
       ref.doi,
       ref.journal,
       ref.nbobject
FROM basic
JOIN has_ref ON basic.oid = has_ref.oidref
JOIN ref ON has_ref.oidbibref = ref.oidbib
WHERE basic.main_id IN ({_quoted_values(main_ids)})
ORDER BY "year" DESC
"""
        table = self._query_tap(query, maxrec=int(max_records))
        return references_from_table(table)

    def _query_tap(self, query: str, *, maxrec: int) -> Any:
        try:
            client = Simbad()
            client.TIMEOUT = int(self._timeout_s)
            return client.query_tap(query, maxrec=maxrec)
        except Exception as exc:
            _log.warning("simbad_query_failed", detail=str(exc), exc_info=exc)
            raise SimbadQueryError(str(exc)) from exc


def objects_from_table(table: Any) -> list[SimbadObject]:
    if table is None or len(table) == 0:
        return []
    objects: list[SimbadObject] = []
    for row in table:
        main_id = _text(row["main_id"])
        ra_deg = _float(row["ra"])
        dec_deg = _float(row["dec"])
        if main_id is None or ra_deg is None or dec_deg is None:
            continue
        separation_deg = _float(row["separation_deg"])
        objects.append(
            SimbadObject(
                main_id=main_id,
                ra_deg=ra_deg,
                dec_deg=dec_deg,
                separation_arcsec=(separation_deg * 3600.0 if separation_deg is not None else None),
                otype=_text(row["otype"]),
                otype_text=_text(row["otype_txt"]),
                spectral_type=_text(row["sp_type"]),
                parallax_mas=_float(row["plx_value"]),
                parallax_error_mas=_float(row["plx_err"]),
                major_axis_arcmin=_float(row["galdim_majaxis"]),
                minor_axis_arcmin=_float(row["galdim_minaxis"]),
                position_angle_deg=_float(row["galdim_angle"]),
                radial_velocity_km_s=_float(row["rvz_radvel"]),
                redshift=_float(row["rvz_redshift"]),
                reference_count=_int(row["nbref"]),
            )
        )
    return objects


def aliases_from_table(table: Any) -> list[SimbadAlias]:
    if table is None or len(table) == 0:
        return []
    aliases: list[SimbadAlias] = []
    for row in table:
        object_id = _text(row["main_id"])
        name = _text(row["id"])
        if object_id is None or name is None:
            continue
        aliases.append(SimbadAlias(object_id=object_id, name=name))
    return aliases


def references_from_table(table: Any) -> list[SimbadReference]:
    if table is None or len(table) == 0:
        return []
    references: list[SimbadReference] = []
    for row in table:
        object_id = _text(row["main_id"])
        bibcode = _text(row["bibcode"])
        if object_id is None or bibcode is None:
            continue
        references.append(
            SimbadReference(
                object_id=object_id,
                bibcode=bibcode,
                year=_int(row["year"]),
                title=_text(row["title"]),
                doi=_text(row["doi"]),
                journal=_text(row["journal"]),
                object_count=_int(row["nbobject"]),
            )
        )
    return references


def _object_type_clause(object_type: str | None) -> str:
    if object_type is None:
        return ""
    if _OBJECT_TYPE_PATTERN.fullmatch(object_type) is None:
        raise ValueError("Invalid SIMBAD object type filter")
    safe_type = object_type.upper().replace("'", "''")
    return f"AND basic.otype = '{safe_type}'"


def _quoted_values(values: list[str]) -> str:
    return ", ".join("'" + value.replace("'", "''") + "'" for value in values)


def _text(value: object) -> str | None:
    if value is None:
        return None
    try:
        if bool(np.ma.is_masked(value)):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    text = str(value).strip()
    if text in {"", "--", "nan", "None"}:
        return None
    return text


def _float(value: object) -> float | None:
    text = _text(value)
    if text is None:
        return None
    try:
        converted = float(text)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(converted):
        return None
    return converted


def _int(value: object) -> int | None:
    converted = _float(value)
    if converted is None:
        return None
    return int(converted)
