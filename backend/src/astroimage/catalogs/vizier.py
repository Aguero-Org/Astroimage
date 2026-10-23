from __future__ import annotations

from typing import Any, Protocol

import astropy.units as u
import numpy as np
from astropy.coordinates import Angle, SkyCoord
from astroquery.vizier import Vizier

from astroimage.catalogs.model import CatalogMetadata, CatalogRow, CatalogTable
from astroimage.shared.logging import catalog_vizier_log as _log

# `+_r` is the angular distance of each row from the query centre; it is the
# same column the reference notebook relies on for the spatial score.
_VIZIER_COLUMNS = ("*", "+_r")
_RA_COLUMNS = ("_RAJ2000", "RAJ2000", "ra", "RA_ICRS")
_DEC_COLUMNS = ("_DEJ2000", "DEJ2000", "dec", "DE_ICRS")


class VizierCatalogProvider(Protocol):
    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
    ) -> list[CatalogTable]: ...

    def catalog_metadata(self, catalogue_id: str) -> CatalogMetadata: ...


class AstroqueryVizierProvider:
    """VizieR access through astroquery, mirroring the reference notebook."""

    def __init__(self, *, timeout_s: float = 120.0) -> None:
        self._timeout_s = timeout_s

    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
    ) -> list[CatalogTable]:
        _log.info(
            "vizier_query",
            center_ra=float(center.ra.deg),
            center_dec=float(center.dec.deg),
            radius_arcsec=radius_arcsec,
            row_limit=row_limit,
        )
        vizier = Vizier(columns=list(_VIZIER_COLUMNS), row_limit=row_limit)
        vizier.TIMEOUT = int(self._timeout_s)
        tables = vizier.query_region(center, radius=Angle(radius_arcsec * u.arcsec))
        return _tables_to_catalogs(tables)

    def catalog_metadata(self, catalogue_id: str) -> CatalogMetadata:
        untitled: CatalogMetadata | None = None
        for candidate in metadata_catalog_candidates(catalogue_id):
            try:
                metadata = Vizier.get_catalog_metadata(catalog=candidate)
            except Exception as exc:
                _log.warning(
                    "vizier_metadata_failed",
                    catalogue_id=catalogue_id,
                    candidate=candidate,
                    detail=str(exc),
                    exc_info=exc,
                )
                continue
            parsed = _metadata_from_table(catalogue_id, metadata)
            if parsed is None:
                continue
            if parsed.title:
                return parsed
            untitled = untitled or parsed
        if untitled is not None:
            return untitled
        return CatalogMetadata(catalogue_id=catalogue_id)


def metadata_catalog_candidates(catalogue_id: str) -> tuple[str, ...]:
    cleaned = catalogue_id.strip().strip("/")
    if not cleaned:
        return ()
    parts = cleaned.split("/")
    candidates = [cleaned]
    if len(parts) >= 3:
        candidates.append("/".join(parts[:-1]))
    return tuple(dict.fromkeys(candidates))


def _metadata_from_table(catalogue_id: str, metadata: Any) -> CatalogMetadata | None:
    if metadata is None or len(metadata) == 0:
        return None
    row = metadata[0]
    return CatalogMetadata(
        catalogue_id=catalogue_id,
        title=_optional(row, "title"),
        authors=_optional(row, "authors"),
        doi=_optional(row, "doi"),
        webpage=_optional(row, "webpage"),
        origin_article=_optional(row, "origin_article"),
    )


def _tables_to_catalogs(tables: Any) -> list[CatalogTable]:
    if tables is None:
        return []
    catalogs: list[CatalogTable] = []
    for table in tables:
        catalogue_id = _catalogue_id(table)
        if not catalogue_id:
            continue
        catalogs.append(_table_to_catalog(catalogue_id, table))
    return catalogs


def _catalogue_id(table: Any) -> str:
    meta = getattr(table, "meta", {}) or {}
    value = meta.get("name") or meta.get("ID") or ""
    return str(value).strip()


def _table_to_catalog(catalogue_id: str, table: Any) -> CatalogTable:
    column_names = tuple(str(name) for name in table.colnames)
    rows: list[CatalogRow] = []
    for index in range(len(table)):
        row = table[index : index + 1]
        rows.append(
            CatalogRow(
                index=index,
                ra_deg=_coordinate(row, column_names, _RA_COLUMNS),
                dec_deg=_coordinate(row, column_names, _DEC_COLUMNS),
                separation_arcsec=_separation_arcsec(row, column_names),
                values=_row_values(row, column_names),
            )
        )
    return CatalogTable(catalogue_id=catalogue_id, column_names=column_names, rows=tuple(rows))


def _coordinate(row: Any, columns: tuple[str, ...], candidates: tuple[str, ...]) -> float | None:
    for name in candidates:
        if name not in columns:
            continue
        value = _float_or_none(row[name])
        if value is not None:
            return value
    return None


def _separation_arcsec(row: Any, columns: tuple[str, ...]) -> float | None:
    if "_r" not in columns:
        return None
    return _float_or_none(row["_r"])


def _row_values(row: Any, columns: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for name in columns:
        text = _text_or_empty(row[name])
        if text:
            values.append((name, text))
    return tuple(values)


def _optional(row: Any, name: str) -> str | None:
    if not hasattr(row, "colnames") or name not in row.colnames:
        return None
    text = _text_or_empty(row[name])
    return text or None


def _text_or_empty(value: object) -> str:
    if value is None or value is np.ma.masked:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    try:
        if bool(np.ma.is_masked(value)):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if text in {"", "--", "nan", "None"}:
        return ""
    return text


def _float_or_none(value: object) -> float | None:
    text = _text_or_empty(value)
    if not text:
        return None
    try:
        converted = float(text)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(converted):
        return None
    return converted
