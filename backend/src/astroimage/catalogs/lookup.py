from __future__ import annotations

import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import astropy.units as u
from astropy.coordinates import SkyCoord

from astroimage.catalogs.download import VIZIER_SOURCE, CatalogDownloadStore
from astroimage.catalogs.evaluation import best_object_row, score_catalogue, select_object_rows
from astroimage.catalogs.model import (
    CatalogEvaluation,
    CatalogMetadata,
    CatalogRow,
    CatalogTable,
)
from astroimage.catalogs.readme import ReadmeFetcher
from astroimage.catalogs.region import region_key
from astroimage.catalogs.schema import CatalogRecommendationConfigSchema
from astroimage.catalogs.vizier import VizierCatalogProvider
from astroimage.shared.logging import catalog_service_log as _log

_README_CONCURRENCY = 8
_readme_executor: ThreadPoolExecutor | None = None


def _readme_pool() -> ThreadPoolExecutor:
    global _readme_executor
    if _readme_executor is None:
        _readme_executor = ThreadPoolExecutor(
            max_workers=_README_CONCURRENCY,
            thread_name_prefix="catalog-readme",
        )
    return _readme_executor


class CatalogLookup:
    def __init__(
        self,
        *,
        provider: VizierCatalogProvider,
        readme_fetcher: ReadmeFetcher,
        query_timeout_s: float,
        downloads: CatalogDownloadStore | None = None,
    ) -> None:
        self._provider = provider
        self._readme_fetcher = readme_fetcher
        self._query_timeout_s = query_timeout_s
        self._downloads = downloads

    async def query_region(
        self,
        center: SkyCoord,
        config: CatalogRecommendationConfigSchema,
    ) -> tuple[list[CatalogTable], str | None]:
        key = region_key(
            ra_deg=float(center.ra.deg),
            dec_deg=float(center.dec.deg),
            radius_arcsec=config.search_radius_arcsec,
            row_limit=config.row_limit,
        )
        if self._downloads is not None:
            hit = await self._downloads.find_fresh(
                source=VIZIER_SOURCE,
                region_key=key,
                ra_deg=float(center.ra.deg),
                dec_deg=float(center.dec.deg),
                radius_arcsec=config.search_radius_arcsec,
                row_limit=config.row_limit,
            )
            if hit is not None:
                stored = (
                    _narrow_to_cone(hit.tables, center, config.search_radius_arcsec)
                    if hit.covered
                    else hit.tables
                )
                _log.info(
                    "catalog_download_hit",
                    region_key=key,
                    catalogues=len(stored),
                    covered=hit.covered,
                )
                return stored, None
        try:
            tables = await asyncio.wait_for(
                asyncio.to_thread(
                    self._provider.query_region,
                    center,
                    config.search_radius_arcsec,
                    row_limit=config.row_limit,
                ),
                timeout=self._query_timeout_s,
            )
        except TimeoutError:
            _log.warning("vizier_query_timed_out", timeout_s=self._query_timeout_s)
            return [], (
                f"La consulta a VizieR superó el límite de {self._query_timeout_s:g} s. "
                "Probá de nuevo en unos minutos."
            )
        except Exception as exc:
            _log.warning("vizier_query_failed", detail=str(exc), exc_info=exc)
            return [], (
                "La consulta a VizieR falló en todos sus servidores. "
                "Probá de nuevo en unos minutos."
            )
        resolved = list(tables)
        if self._downloads is not None:
            await self._downloads.replace(
                source=VIZIER_SOURCE,
                region_key=key,
                ra_deg=float(center.ra.deg),
                dec_deg=float(center.dec.deg),
                radius_arcsec=config.search_radius_arcsec,
                row_limit=config.row_limit,
                tables=resolved,
            )
        return resolved, None

    def evaluate_table(
        self,
        table: CatalogTable,
        *,
        known_identifiers: list[str],
        include_papers: bool,
        search_radius_arcsec: float,
    ) -> CatalogEvaluation:
        object_rows = select_object_rows(table, known_identifiers, search_radius_arcsec)
        best = best_object_row(object_rows)
        metadata = (
            self._provider.catalog_metadata(table.catalogue_id)
            if include_papers
            else CatalogMetadata(catalogue_id=table.catalogue_id)
        )
        readme = self._readme_fetcher.fetch(table.catalogue_id) if include_papers else None
        return score_catalogue(table.catalogue_id, metadata, readme, best)

    def fallback_evaluation(
        self,
        table: CatalogTable,
        config: CatalogRecommendationConfigSchema,
    ) -> CatalogEvaluation:
        return self.evaluate_table(
            table,
            known_identifiers=config.identifiers,
            include_papers=False,
            search_radius_arcsec=config.search_radius_arcsec,
        )

    async def evaluate_tables(
        self,
        tables: list[CatalogTable],
        config: CatalogRecommendationConfigSchema,
    ) -> list[tuple[CatalogEvaluation, CatalogTable]]:
        selected = tables[: config.max_catalogues]
        loop = asyncio.get_running_loop()
        futures = [
            loop.run_in_executor(
                _readme_pool(),
                functools.partial(
                    self.evaluate_table,
                    table,
                    known_identifiers=config.identifiers,
                    include_papers=config.include_papers,
                    search_radius_arcsec=config.search_radius_arcsec,
                ),
            )
            for table in selected
        ]
        results = await asyncio.gather(*futures, return_exceptions=True)
        pairs: list[tuple[CatalogEvaluation, CatalogTable]] = []
        for table, result in zip(selected, results, strict=True):
            if isinstance(result, BaseException):
                _log.warning(
                    "vizier_catalogue_failed",
                    catalogue_id=table.catalogue_id,
                    detail=str(result),
                )
                pairs.append((self.fallback_evaluation(table, config), table))
            else:
                pairs.append((result, table))
        return pairs


def _narrow_to_cone(
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
        ra=[ra for _, ra, _ in located] * u.deg,
        dec=[dec for _, _, dec in located] * u.deg,
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
