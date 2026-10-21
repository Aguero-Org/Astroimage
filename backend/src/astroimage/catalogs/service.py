from __future__ import annotations

import asyncio
import functools
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from astroimage.catalogs.cache import CatalogRecommendationCache, recommendation_cache_key
from astroimage.catalogs.crossmatch import crossmatch_catalog
from astroimage.catalogs.model import (
    CatalogCrossmatch,
    CatalogEvaluation,
    CatalogMetadata,
    CatalogRow,
    CatalogTable,
    DetectionCoordinate,
)
from astroimage.catalogs.readme import (
    ReadmeData,
    ReadmeFetcher,
    ads_url,
    clean_bibcode,
    clean_doi,
    determine_catalogue_bibcode,
    determine_paper_bibcode,
    determine_paper_doi,
    doi_url,
)
from astroimage.catalogs.schema import (
    CatalogCrossmatchSchema,
    CatalogRecommendationConfigSchema,
    CatalogRecommendationItemSchema,
    CatalogRecommendationResponse,
    CatalogRecommendationSummarySchema,
    CrossmatchRowSchema,
)
from astroimage.catalogs.scoring import (
    classify_match,
    doi_score,
    find_identifiers_in_row,
    identifier_score,
    paper_score,
    separation_score,
    total_score,
)
from astroimage.catalogs.vizier import VizierCatalogProvider
from astroimage.fits.reader import FitsReader
from astroimage.fits.service import FitsService
from astroimage.fits.wcs import field_center, to_sky, world_coordinates
from astroimage.shared.logging import catalog_service_log as _log
from astroimage.sources.service import SourceDetectionService

_VIZIER_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="vizier")
_README_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="catalog-readme")
_DEFAULT_QUERY_TIMEOUT_S = 180.0


@dataclass(frozen=True)
class _ObjectRow:
    row: CatalogRow
    identifiers: tuple[str, ...]
    columns: tuple[str, ...]
    spatial_match: bool
    identifier_match: bool


@dataclass(frozen=True)
class _BestMatch:
    separation_arcsec: float | None
    object_identifier: str | None
    identifier_columns: str | None
    spatial_match: bool
    identifier_match: bool


class _DetectedSource(Protocol):
    @property
    def source_id(self) -> int: ...

    @property
    def xcentroid(self) -> float: ...

    @property
    def ycentroid(self) -> float: ...


class CatalogRecommendationService:
    def __init__(
        self,
        *,
        fits: FitsService,
        detection: SourceDetectionService | None = None,
        provider: VizierCatalogProvider,
        readme_fetcher: ReadmeFetcher,
        cache: CatalogRecommendationCache,
        reader: FitsReader | None = None,
        query_timeout_s: float = _DEFAULT_QUERY_TIMEOUT_S,
    ) -> None:
        self._fits = fits
        self._detection = detection
        self._provider = provider
        self._readme_fetcher = readme_fetcher
        self._cache = cache
        self._reader = reader or FitsReader()
        self._query_timeout_s = query_timeout_s

    async def ensure_record(self, record_id: UUID) -> None:
        await self._fits.get_record(record_id)

    async def recommend_from_record(
        self,
        record_id: UUID,
        *,
        client_id: str = "anonymous",
        hdu_index: int | None = None,
        config: CatalogRecommendationConfigSchema | None = None,
    ) -> CatalogRecommendationResponse:
        resolved = config or CatalogRecommendationConfigSchema()
        key = recommendation_cache_key(
            record_id=record_id,
            client_id=client_id,
            hdu_index=hdu_index,
            config=resolved,
        )
        cached = self._cache.get(key)
        if cached is not None:
            _log.info("catalog_cache_hit", record_id=str(record_id), client_id=client_id)
            return cached
        record = await self._fits.get_record(record_id)
        payload = await self._fits.get_payload(record)
        result = await self.recommend(
            payload,
            source_name=record.original_filename,
            hdu_index=hdu_index,
            client_id=client_id,
            config=resolved,
            record_id=record_id,
        )
        self._cache.set(key, result)
        return result

    async def recommend(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
        client_id: str = "anonymous",
        config: CatalogRecommendationConfigSchema | None = None,
        record_id: UUID | None = None,
    ) -> CatalogRecommendationResponse:
        resolved = config or CatalogRecommendationConfigSchema()
        metadata = self._reader.read_metadata_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )
        wcs = world_coordinates(metadata)
        if wcs is None:
            _log.info(
                "catalog_recommend_skipped", reason="no wcs", source_name=metadata.source_name
            )
            return CatalogRecommendationResponse(
                status="completed",
                source_name=metadata.source_name,
                radius_arcsec=resolved.search_radius_arcsec,
                include_papers=resolved.include_papers,
                wcs_present=False,
                queried=False,
            )
        center = field_center(wcs)
        tables, error = await self._query_vizier(center, resolved)
        if error is not None:
            return CatalogRecommendationResponse(
                status="completed",
                source_name=metadata.source_name,
                ra_deg=float(center.ra.deg),
                dec_deg=float(center.dec.deg),
                radius_arcsec=resolved.search_radius_arcsec,
                include_papers=resolved.include_papers,
                wcs_present=True,
                queried=False,
                error=error,
            )

        pairs = await self._evaluate_tables(tables, resolved)
        ranked = self._rank(pairs)
        tables_by_id = {table.catalogue_id: table for _, table in pairs}
        detections = await self._detections(
            record_id,
            wcs,
            hdu_index,
            client_id=client_id,
            enabled=resolved.crossmatch,
        )
        crossmatches = self._crossmatches(ranked, tables_by_id, resolved, detections)
        recommendations = self._to_schema(ranked, crossmatches)
        return self._response(metadata.source_name, center, resolved, recommendations)

    async def _query_vizier(
        self,
        center: SkyCoord,
        config: CatalogRecommendationConfigSchema,
    ) -> tuple[list[CatalogTable], str | None]:
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(
            _VIZIER_EXECUTOR,
            functools.partial(
                self._provider.query_region,
                center,
                config.search_radius_arcsec,
                row_limit=config.row_limit,
            ),
        )
        try:
            tables = await asyncio.wait_for(future, timeout=self._query_timeout_s)
        except TimeoutError:
            _log.warning("vizier_query_timed_out", timeout_s=self._query_timeout_s)
            return [], f"VizieR query timed out after {self._query_timeout_s} seconds"
        except Exception as exc:
            _log.warning("vizier_query_failed", detail=str(exc), exc_info=exc)
            return [], f"VizieR query failed: {exc}"
        return list(tables), None

    async def _evaluate_tables(
        self,
        tables: list[CatalogTable],
        config: CatalogRecommendationConfigSchema,
    ) -> list[tuple[CatalogEvaluation, CatalogTable]]:
        selected = tables[: config.max_catalogues]
        loop = asyncio.get_running_loop()
        futures = [
            loop.run_in_executor(
                _README_EXECUTOR,
                functools.partial(
                    self._evaluate_table,
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
                pairs.append(
                    (self._fallback_evaluation(table, config), table),
                )
            else:
                pairs.append((result, table))
        return pairs

    def _evaluate_table(
        self,
        table: CatalogTable,
        *,
        known_identifiers: list[str],
        include_papers: bool,
        search_radius_arcsec: float,
    ) -> CatalogEvaluation:
        object_rows = self._object_rows(table, known_identifiers, search_radius_arcsec)
        best = self._best_object_row(object_rows)
        metadata = (
            self._provider.catalog_metadata(table.catalogue_id)
            if include_papers
            else CatalogMetadata(catalogue_id=table.catalogue_id)
        )
        readme = self._readme_fetcher.fetch(table.catalogue_id) if include_papers else None
        return self._score(table.catalogue_id, metadata, readme, best)

    def _fallback_evaluation(
        self,
        table: CatalogTable,
        config: CatalogRecommendationConfigSchema,
    ) -> CatalogEvaluation:
        return self._evaluate_table(
            table,
            known_identifiers=config.identifiers,
            include_papers=False,
            search_radius_arcsec=config.search_radius_arcsec,
        )

    @staticmethod
    def _object_rows(
        table: CatalogTable,
        known_identifiers: list[str],
        search_radius_arcsec: float,
    ) -> list[_ObjectRow]:
        rows: list[_ObjectRow] = []
        for row in table.rows:
            identifiers, columns = find_identifiers_in_row(row.values, known_identifiers)
            spatial_match = (
                row.separation_arcsec is not None and row.separation_arcsec <= search_radius_arcsec
            )
            identifier_match = len(identifiers) > 0
            if spatial_match or identifier_match:
                rows.append(
                    _ObjectRow(
                        row=row,
                        identifiers=identifiers,
                        columns=columns,
                        spatial_match=spatial_match,
                        identifier_match=identifier_match,
                    )
                )
        return rows

    @staticmethod
    def _best_object_row(object_rows: list[_ObjectRow]) -> _ObjectRow | None:
        if not object_rows:
            return None
        return min(
            object_rows,
            key=lambda entry: (
                0 if entry.identifier_match else 1,
                entry.row.separation_arcsec if entry.row.separation_arcsec is not None else np.inf,
            ),
        )

    @staticmethod
    def _best_match(best: _ObjectRow | None) -> _BestMatch:
        if best is None:
            return _BestMatch(None, None, None, False, False)
        return _BestMatch(
            separation_arcsec=best.row.separation_arcsec,
            object_identifier="; ".join(best.identifiers) if best.identifiers else None,
            identifier_columns="; ".join(best.columns) if best.columns else None,
            spatial_match=bool(best.spatial_match),
            identifier_match=bool(best.identifier_match),
        )

    def _score(
        self,
        catalogue_id: str,
        metadata: CatalogMetadata,
        readme: ReadmeData | None,
        best: _ObjectRow | None,
    ) -> CatalogEvaluation:
        readme_data = readme or ReadmeData()
        catalogue_bibcode = determine_catalogue_bibcode(metadata.origin_article, readme_data)
        paper_bibcode = determine_paper_bibcode(metadata.origin_article, readme_data)
        paper_doi = determine_paper_doi(paper_bibcode, readme_data, metadata.doi)
        catalogue_doi = clean_doi(metadata.doi)
        match = self._best_match(best)
        spatial = separation_score(match.separation_arcsec)
        identifier = identifier_score(match.identifier_match)
        paper = paper_score(paper_bibcode)
        doi = doi_score(paper_doi)
        description = readme_data.description or readme_data.abstract
        return CatalogEvaluation(
            catalogue_id=catalogue_id,
            metadata=metadata,
            match_type=classify_match(match.identifier_match, paper_bibcode or None),
            catalogue_description=description or None,
            catalogue_keywords=readme_data.keywords or None,
            separation_arcsec=match.separation_arcsec,
            object_found_in_table=match.identifier_match,
            object_identifier=match.object_identifier,
            identifier_columns=match.identifier_columns,
            spatial_match=match.spatial_match,
            identifier_match=match.identifier_match,
            spatial_score=spatial,
            identifier_score=identifier,
            paper_score=paper,
            doi_score=doi,
            total_score=total_score(spatial=spatial, identifier=identifier, paper=paper, doi=doi),
            catalogue_bibcode=clean_bibcode(catalogue_bibcode) or None,
            catalogue_doi=catalogue_doi or None,
            catalogue_doi_url=doi_url(catalogue_doi),
            paper_bibcode=clean_bibcode(paper_bibcode) or None,
            paper_doi=paper_doi or None,
            paper_doi_url=doi_url(paper_doi),
            paper_ads_url=ads_url(paper_bibcode),
            vizier_url=metadata.webpage,
            readme_url=readme_data.url,
            readme_bibcodes=readme_data.bibcodes,
            readme_dois=readme_data.dois,
        )

    @staticmethod
    def _rank(
        pairs: list[tuple[CatalogEvaluation, CatalogTable]],
    ) -> list[CatalogEvaluation]:
        ordered = sorted(
            pairs,
            key=lambda pair: (
                -pair[0].total_score,
                not pair[0].object_found_in_table,
                not pair[0].identifier_match,
                pair[0].separation_arcsec if pair[0].separation_arcsec is not None else np.inf,
            ),
        )
        return [evaluation for evaluation, _ in ordered]

    async def _detections(
        self,
        record_id: UUID | None,
        wcs: WCS,
        hdu_index: int | None,
        *,
        client_id: str,
        enabled: bool,
    ) -> list[DetectionCoordinate]:
        if not enabled or self._detection is None or record_id is None:
            return []
        result = await self._detection.detect_from_record(
            record_id,
            client_id=client_id,
            hdu_index=hdu_index,
        )
        return self._detection_coordinates(wcs, result.point_sources, result.extended_sources)

    @staticmethod
    def _detection_coordinates(
        wcs: WCS,
        point_sources: Sequence[_DetectedSource],
        extended_sources: Sequence[_DetectedSource],
    ) -> list[DetectionCoordinate]:
        detections: list[DetectionCoordinate] = []
        for point in point_sources:
            coord = to_sky(wcs, point.xcentroid, point.ycentroid)
            detections.append(
                DetectionCoordinate(
                    source_id=point.source_id,
                    object_type="point",
                    ra_deg=float(coord.ra.deg),
                    dec_deg=float(coord.dec.deg),
                )
            )
        for extended in extended_sources:
            coord = to_sky(wcs, extended.xcentroid, extended.ycentroid)
            detections.append(
                DetectionCoordinate(
                    source_id=extended.source_id,
                    object_type="extended",
                    ra_deg=float(coord.ra.deg),
                    dec_deg=float(coord.dec.deg),
                )
            )
        return detections

    def _crossmatches(
        self,
        evaluations: list[CatalogEvaluation],
        tables_by_id: dict[str, CatalogTable],
        config: CatalogRecommendationConfigSchema,
        detections: list[DetectionCoordinate],
    ) -> dict[str, CatalogCrossmatch]:
        if not config.crossmatch or not detections:
            return {}
        crossmatches: dict[str, CatalogCrossmatch] = {}
        for evaluation in evaluations[: config.crossmatch_top]:
            table = tables_by_id.get(evaluation.catalogue_id)
            if table is None:
                continue
            crossmatches[evaluation.catalogue_id] = crossmatch_catalog(
                evaluation.catalogue_id,
                table.rows,
                detections,
                match_radius_arcsec=config.crossmatch_radius_arcsec,
            )
        return crossmatches

    @staticmethod
    def _to_crossmatch_schema(crossmatch: CatalogCrossmatch) -> CatalogCrossmatchSchema:
        return CatalogCrossmatchSchema(
            catalogue_id=crossmatch.catalogue_id,
            match_radius_arcsec=crossmatch.match_radius_arcsec,
            detection_count=crossmatch.detection_count,
            matched_count=crossmatch.matched_count,
            matches=[
                CrossmatchRowSchema(
                    catalogue_row_index=row.catalogue_row_index,
                    ra_deg=row.ra_deg,
                    dec_deg=row.dec_deg,
                    object_identifier=row.object_identifier,
                    detection_source_id=row.detection_source_id,
                    object_type=row.object_type,
                    separation_arcsec=row.separation_arcsec,
                    matched=row.matched,
                    probability=row.probability,
                )
                for row in crossmatch.matches
            ],
        )

    def _to_schema(
        self,
        evaluations: list[CatalogEvaluation],
        crossmatches: dict[str, CatalogCrossmatch],
    ) -> list[CatalogRecommendationItemSchema]:
        items: list[CatalogRecommendationItemSchema] = []
        for rank, evaluation in enumerate(evaluations, start=1):
            crossmatch = crossmatches.get(evaluation.catalogue_id)
            items.append(
                CatalogRecommendationItemSchema(
                    rank=rank,
                    catalogue_id=evaluation.catalogue_id,
                    match_type=evaluation.match_type,
                    separation_arcsec=evaluation.separation_arcsec,
                    object_found_in_table=evaluation.object_found_in_table,
                    object_identifier=evaluation.object_identifier,
                    identifier_columns=evaluation.identifier_columns,
                    spatial_match=evaluation.spatial_match,
                    identifier_match=evaluation.identifier_match,
                    spatial_score=evaluation.spatial_score,
                    identifier_score=evaluation.identifier_score,
                    paper_score=evaluation.paper_score,
                    doi_score=evaluation.doi_score,
                    total_score=evaluation.total_score,
                    catalogue_title=evaluation.metadata.title,
                    catalogue_authors=evaluation.metadata.authors,
                    catalogue_description=evaluation.catalogue_description,
                    catalogue_keywords=evaluation.catalogue_keywords,
                    catalogue_bibcode=evaluation.catalogue_bibcode,
                    catalogue_doi=evaluation.catalogue_doi,
                    catalogue_doi_url=evaluation.catalogue_doi_url,
                    paper_bibcode=evaluation.paper_bibcode,
                    paper_doi=evaluation.paper_doi,
                    paper_doi_url=evaluation.paper_doi_url,
                    paper_ads_url=evaluation.paper_ads_url,
                    vizier_url=evaluation.vizier_url,
                    readme_url=evaluation.readme_url,
                    readme_bibcodes=list(evaluation.readme_bibcodes),
                    readme_dois=list(evaluation.readme_dois),
                    crossmatch=(
                        self._to_crossmatch_schema(crossmatch) if crossmatch is not None else None
                    ),
                )
            )
        return items

    @staticmethod
    def _response(
        source_name: str | None,
        center: SkyCoord,
        config: CatalogRecommendationConfigSchema,
        recommendations: list[CatalogRecommendationItemSchema],
    ) -> CatalogRecommendationResponse:
        return CatalogRecommendationResponse(
            status="completed",
            source_name=source_name,
            ra_deg=float(center.ra.deg),
            dec_deg=float(center.dec.deg),
            radius_arcsec=config.search_radius_arcsec,
            include_papers=config.include_papers,
            wcs_present=True,
            queried=True,
            summary=CatalogRecommendationSummarySchema(
                catalogue_count=len(recommendations),
                object_in_table_count=sum(
                    1 for item in recommendations if item.object_found_in_table
                ),
                queried_catalogue_count=len(recommendations),
            ),
            recommendations=recommendations,
        )
