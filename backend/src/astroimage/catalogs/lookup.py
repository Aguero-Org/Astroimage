from __future__ import annotations

import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

from astropy.coordinates import SkyCoord

from astroimage.catalogs.evaluation import best_object_row, score_catalogue, select_object_rows
from astroimage.catalogs.model import CatalogEvaluation, CatalogMetadata, CatalogTable
from astroimage.catalogs.readme import ReadmeFetcher
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
    ) -> None:
        self._provider = provider
        self._readme_fetcher = readme_fetcher
        self._query_timeout_s = query_timeout_s

    async def query_region(
        self,
        center: SkyCoord,
        config: CatalogRecommendationConfigSchema,
    ) -> tuple[list[CatalogTable], str | None]:
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
            return [], f"VizieR query timed out after {self._query_timeout_s} seconds"
        except Exception as exc:
            _log.warning("vizier_query_failed", detail=str(exc), exc_info=exc)
            return [], f"VizieR query failed: {exc}"
        return list(tables), None

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
