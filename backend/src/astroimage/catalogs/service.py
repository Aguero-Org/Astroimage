from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from astroimage.catalogs.cache import CatalogRecommendationCache, recommendation_cache_key
from astroimage.catalogs.crossmatch import crossmatch_catalog
from astroimage.catalogs.download import CatalogDownloadStore
from astroimage.catalogs.evaluation import rank_evaluations
from astroimage.catalogs.lookup import CatalogLookup
from astroimage.catalogs.model import (
    CatalogCrossmatch,
    CatalogEvaluation,
    CatalogTable,
    DetectionCoordinate,
)
from astroimage.catalogs.readme import ReadmeFetcher
from astroimage.catalogs.schema import (
    CatalogCrossmatchSchema,
    CatalogRecommendationConfigSchema,
    CatalogRecommendationItemSchema,
    CatalogRecommendationResponse,
    CatalogRecommendationSummarySchema,
    CrossmatchRowSchema,
)
from astroimage.catalogs.vizier import VizierCatalogProvider
from astroimage.fits.reader import FitsReader
from astroimage.fits.service import FitsService
from astroimage.fits.wcs import field_center, to_sky, world_coordinates
from astroimage.shared.logging import catalog_service_log as _log
from astroimage.sources.service import SourceDetectionService

_DEFAULT_QUERY_TIMEOUT_S = 180.0


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
        downloads: CatalogDownloadStore | None = None,
    ) -> None:
        self._fits = fits
        self._detection = detection
        self._cache = cache
        self._reader = reader or FitsReader()
        self._lookup = CatalogLookup(
            provider=provider,
            readme_fetcher=readme_fetcher,
            query_timeout_s=query_timeout_s,
            downloads=downloads,
        )

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
        tables, error = await self._lookup.query_region(center, resolved)
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

        pairs = await self._lookup.evaluate_tables(tables, resolved)
        ranked = rank_evaluations(pairs)
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
