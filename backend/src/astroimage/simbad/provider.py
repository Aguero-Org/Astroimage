from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any, Protocol

import numpy as np
from astropy.coordinates import SkyCoord
from astroquery.simbad import SimbadClass

from astroimage.shared.logging import simbad_provider_log as _log
from astroimage.simbad.model import SimbadAlias, SimbadObject, SimbadReference

_OBJECT_TYPE_PATTERN = re.compile(r"^[A-Za-z0-9_+.\-]{1,32}$")
_SIMBAD_SERVERS = ("simbad.cds.unistra.fr", "simbad.harvard.edu")
_SERVER_TIMEOUT_S = 60


def _with_transport_timeout(client: Any, timeout_s: float) -> None:
    """Bound the TAP HTTP calls astroquery performs through the PyVO session.

    Astroquery's ``SimbadClass.query_tap`` reaches SIMBAD through a PyVO
    ``TAPService`` that shares the client's ``requests`` session. Capability
    discovery and synchronous queries would otherwise wait without an HTTP
    timeout, so a stalled server never yields to the next one. The uppercase
    ``TIMEOUT`` attribute does not bound those requests.
    """
    session = getattr(client, "_session", None)
    request = getattr(session, "request", None)
    if session is None or request is None:
        return

    def timed_request(method: str, url: str, **kwargs: Any) -> Any:
        kwargs.setdefault("timeout", timeout_s)
        return request(method, url, **kwargs)

    session.request = timed_request


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
    def __init__(
        self,
        *,
        timeout_s: float = 120.0,
        servers: Sequence[str] | None = None,
    ) -> None:
        configured = tuple(server.strip() for server in servers or () if server.strip())
        self._servers = configured or _SIMBAD_SERVERS
        self._server_timeout_s = max(
            1,
            min(int(timeout_s / len(self._servers)), _SERVER_TIMEOUT_S),
        )

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
        last_error: Exception | None = None
        for server in self._servers:
            _log.info("simbad_query", server=server, maxrec=maxrec)
            try:
                client = SimbadClass()
                client.server = server
                _with_transport_timeout(client, float(self._server_timeout_s))
                table = client.query_tap(query, maxrec=maxrec)
            except Exception as exc:
                _log.warning("simbad_server_failed", server=server, exc_info=exc)
                last_error = exc
                continue
            _log.info("simbad_query_ok", server=server)
            return table
        if last_error is not None:
            raise SimbadQueryError(str(last_error)) from last_error
        raise SimbadQueryError("No SIMBAD servers configured")


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
