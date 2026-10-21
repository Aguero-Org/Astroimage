from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

import astropy.units as u
import numpy as np
import structlog
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from opentelemetry import trace

from astroimage.fits.reader import FitsReader
from astroimage.fits.service import FitsService
from astroimage.fits.wcs import to_sky, world_coordinates
from astroimage.sources.detection_service import (
    FITS_SERVICE_NOT_CONFIGURED,
    SourceDetectionService,
)
from astroimage.sources.gaia import (
    AstroqueryGaiaProvider,
    GaiaCatalogProvider,
    GaiaObject,
    GaiaQueryError,
    GaiaSourceMatch,
    match_sources_to_gaia,
    search_radius_arcsec,
)
from astroimage.sources.model import ExtendedSource, PointSource, SourceDetectionResult
from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    GaiaMatchConfigSchema,
    GaiaMatchSchema,
    GaiaTypeSummarySchema,
    GaiaVerificationResponse,
    GaiaVerificationSummarySchema,
    PointDetectionConfigSchema,
)

_log = structlog.get_logger("astroimage.sources.gaia")
_tracer = trace.get_tracer("astroimage.sources.gaia")
_GAIA_QUERY_TIMEOUT_S = 120.0
_GAIA_CONCURRENCY = 8
_gaia_executor = ThreadPoolExecutor(
    max_workers=_GAIA_CONCURRENCY,
    thread_name_prefix="gaia",
)


@dataclass(frozen=True)
class _SourceEntry:
    source_id: int
    object_type: Literal["point", "extended"]
    rank: int
    coordinate: SkyCoord | None


def _mean_coordinate(detected_coords: list[SkyCoord]) -> SkyCoord:
    return SkyCoord(
        ra=float(np.mean([coord.ra.deg for coord in detected_coords])) * u.deg,
        dec=float(np.mean([coord.dec.deg for coord in detected_coords])) * u.deg,
        frame="icrs",
    )


def _empty_match() -> GaiaSourceMatch:
    return GaiaSourceMatch(
        separation_arcsec=None,
        probability=0.0,
        matched=False,
        gaia_source_id=None,
        gaia_ra_deg=None,
        gaia_dec_deg=None,
        gaia_gmag=None,
    )


def _to_match_schema(entry: _SourceEntry, match: GaiaSourceMatch) -> GaiaMatchSchema:
    return GaiaMatchSchema(
        source_id=entry.source_id,
        object_type=entry.object_type,
        rank=entry.rank,
        ra_deg=float(entry.coordinate.ra.deg) if entry.coordinate is not None else None,
        dec_deg=float(entry.coordinate.dec.deg) if entry.coordinate is not None else None,
        gaia_match=match.matched,
        gaia_separation_arcsec=match.separation_arcsec,
        gaia_probability=match.probability,
        gaia_source_id=match.gaia_source_id,
        gaia_ra_deg=match.gaia_ra_deg,
        gaia_dec_deg=match.gaia_dec_deg,
        gaia_gmag=match.gaia_gmag,
    )


@dataclass(frozen=True)
class _Prepared:
    source_name: str | None
    wcs: WCS | None
    entries: list[_SourceEntry]
    entry_coords: list[SkyCoord]
    match_config: GaiaMatchConfigSchema


def _partition_coords(
    coords: list[SkyCoord],
    num_blocks: int,
) -> list[list[SkyCoord]]:
    per_block, extra = divmod(len(coords), num_blocks)
    partitions: list[list[SkyCoord]] = []
    start = 0
    for index in range(num_blocks):
        size = per_block + (1 if index < extra else 0)
        end = start + size
        partitions.append(coords[start:end])
        start = end
    return partitions


def _block_queries(
    coords: list[SkyCoord],
    *,
    match_radius_arcsec: float,
) -> list[tuple[SkyCoord, float]]:
    ordered = sorted(coords, key=lambda coord: (float(coord.ra.deg), float(coord.dec.deg)))
    count = min(_GAIA_CONCURRENCY, len(ordered))
    queries: list[tuple[SkyCoord, float]] = []
    for chunk in _partition_coords(ordered, count):
        center = _mean_coordinate(chunk)
        radius = search_radius_arcsec(
            center,
            chunk,
            match_radius_arcsec=match_radius_arcsec,
        )
        queries.append((center, radius))
    return queries


def _merge_gaia_objects(results: list[list[GaiaObject]]) -> list[GaiaObject]:
    merged: list[GaiaObject] = []
    seen: set[str] = set()
    for block in results:
        for gaia_object in block:
            if gaia_object.source_id in seen:
                continue
            seen.add(gaia_object.source_id)
            merged.append(gaia_object)
    return merged


async def _search_block(
    provider: GaiaCatalogProvider,
    center: SkyCoord,
    radius: float,
) -> list[GaiaObject]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_gaia_executor, provider.search_cone, center, radius)


class GaiaVerificationService:
    def __init__(
        self,
        detection_service: SourceDetectionService,
        fits: FitsService | None = None,
        provider: GaiaCatalogProvider | None = None,
        reader: FitsReader | None = None,
        query_timeout_s: float = _GAIA_QUERY_TIMEOUT_S,
    ) -> None:
        self._detection = detection_service
        self._fits = fits
        self.provider = provider or AstroqueryGaiaProvider()
        self._reader = reader or FitsReader()
        self._query_timeout_s = query_timeout_s

    async def ensure_record(self, record_id: UUID) -> None:
        if self._fits is None:
            raise RuntimeError(FITS_SERVICE_NOT_CONFIGURED)
        await self._fits.get_record(record_id)

    async def verify_from_record(
        self,
        record_id: UUID,
        *,
        client_id: str = "anonymous",
        hdu_index: int | None = None,
        config: PointDetectionConfigSchema | None = None,
        extended_config: ExtendedDetectionConfigSchema | None = None,
        gaia_config: GaiaMatchConfigSchema | None = None,
    ) -> GaiaVerificationResponse:
        if self._fits is None:
            raise RuntimeError(FITS_SERVICE_NOT_CONFIGURED)
        detection_result = await self._detection.resolve_detection_from_record(
            record_id,
            client_id=client_id,
            hdu_index=hdu_index,
            config=config,
            extended_config=extended_config,
        )
        record = await self._fits.get_record(record_id)
        payload = await self._fits.get_payload(record)
        _log.info("gaia_verify_running", record_id=str(record_id))
        with _tracer.start_as_current_span("source_gaia_verification") as span:
            prepared = self._prepare(
                payload,
                source_name=record.original_filename,
                hdu_index=hdu_index,
                detection_result=detection_result,
                gaia_config=gaia_config,
            )
            response = await self._query_blocks(prepared, record_id=record_id)
            span.set_attribute(
                "matched_count",
                sum(1 for row in response.matches if row.gaia_match),
            )
            span.set_attribute("queried", response.queried)
            return response

    async def _query_blocks(
        self,
        prepared: _Prepared,
        *,
        record_id: UUID,
    ) -> GaiaVerificationResponse:
        if prepared.wcs is None or not prepared.entry_coords:
            return self._finish(prepared, [], queried=False, error=None)
        block_queries = _block_queries(
            prepared.entry_coords,
            match_radius_arcsec=prepared.match_config.match_radius_arcsec,
        )
        futures = [_search_block(self.provider, center, radius) for center, radius in block_queries]
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*futures, return_exceptions=True),
                timeout=self._query_timeout_s,
            )
        except TimeoutError:
            _log.warning(
                "gaia_query_timed_out",
                record_id=str(record_id),
                timeout_s=self._query_timeout_s,
                blocks=len(block_queries),
            )
            return self._finish(
                prepared,
                [],
                queried=False,
                error=f"Gaia query timed out after {self._query_timeout_s} seconds",
            )
        failures = [result for result in results if isinstance(result, Exception)]
        if failures:
            _log.warning("gaia_provider_error", detail=str(failures[0]))
            return self._finish(
                prepared,
                [],
                queried=False,
                error=f"Gaia query failed: {failures[0]}",
            )
        objects = _merge_gaia_objects([result for result in results if isinstance(result, list)])
        if not objects:
            _log.info("gaia_fallback_triggered", record_id=str(record_id))
            fallback_center = _mean_coordinate(prepared.entry_coords)
            fallback_radius = search_radius_arcsec(
                fallback_center,
                prepared.entry_coords,
                match_radius_arcsec=prepared.match_config.match_radius_arcsec,
            )
            try:
                fallback_objects = await _search_block(
                    self.provider,
                    fallback_center,
                    fallback_radius,
                )
            except GaiaQueryError as exc:
                _log.warning("gaia_fallback_failed", detail=str(exc))
                fallback_objects = []
            if fallback_objects:
                _log.info("gaia_fallback_recovered", n=len(fallback_objects))
                objects = _merge_gaia_objects([fallback_objects])
        return self._finish(prepared, objects, queried=True, error=None)

    def verify(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
        config: PointDetectionConfigSchema | None = None,
        extended_config: ExtendedDetectionConfigSchema | None = None,
        gaia_config: GaiaMatchConfigSchema | None = None,
        detection_result: SourceDetectionResult | None = None,
    ) -> GaiaVerificationResponse:
        with _tracer.start_as_current_span("source_gaia_verification") as span:
            resolved_detection = detection_result or self._detection.detect(
                payload,
                source_name=source_name,
                hdu_index=hdu_index,
                config=config,
                extended_config=extended_config,
            )
            prepared = self._prepare(
                payload,
                source_name=source_name,
                hdu_index=hdu_index,
                detection_result=resolved_detection,
                gaia_config=gaia_config,
            )
            objects: list[GaiaObject] = []
            error: str | None = None
            queried = False
            if prepared.wcs is not None and prepared.entry_coords:
                center = _mean_coordinate(prepared.entry_coords)
                radius = search_radius_arcsec(
                    center,
                    prepared.entry_coords,
                    match_radius_arcsec=prepared.match_config.match_radius_arcsec,
                )
                try:
                    objects = self.provider.search_cone(center, radius)
                except GaiaQueryError as exc:
                    _log.warning("gaia_provider_error", detail=str(exc))
                    error = f"Gaia query failed: {exc}"
                queried = error is None
            response = self._finish(prepared, objects, queried=queried, error=error)
            span.set_attribute(
                "matched_count",
                sum(1 for row in response.matches if row.gaia_match),
            )
            span.set_attribute("queried", queried)
            return response

    def _prepare(
        self,
        payload: bytes,
        *,
        source_name: str | None,
        hdu_index: int | None,
        detection_result: SourceDetectionResult,
        gaia_config: GaiaMatchConfigSchema | None,
    ) -> _Prepared:
        match_config = gaia_config or GaiaMatchConfigSchema()
        metadata = self._reader.read_metadata_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )
        wcs = world_coordinates(metadata)
        entries = self._entries(
            detection_result.point_sources,
            detection_result.extended_sources,
            wcs,
        )
        entry_coords = [entry.coordinate for entry in entries if entry.coordinate is not None]
        return _Prepared(
            source_name=metadata.source_name,
            wcs=wcs,
            entries=entries,
            entry_coords=entry_coords,
            match_config=match_config,
        )

    def _matches(
        self,
        prepared: _Prepared,
        objects: list[GaiaObject],
    ) -> list[GaiaMatchSchema]:
        if prepared.wcs is None or not prepared.entry_coords:
            return [_to_match_schema(entry, _empty_match()) for entry in prepared.entries]
        raw_matches = match_sources_to_gaia(
            prepared.entry_coords,
            objects,
            match_radius_arcsec=prepared.match_config.match_radius_arcsec,
            probability_power=prepared.match_config.probability_power,
        )
        return [
            _to_match_schema(entry, match)
            for entry, match in zip(prepared.entries, raw_matches, strict=True)
        ]

    def _finish(
        self,
        prepared: _Prepared,
        objects: list[GaiaObject],
        *,
        queried: bool,
        error: str | None,
    ) -> GaiaVerificationResponse:
        matches = self._matches(prepared, objects)
        point_rows = [row for row in matches if row.object_type == "point"]
        extended_rows = [row for row in matches if row.object_type == "extended"]
        _log.info(
            "gaia_verify_complete",
            source_name=prepared.source_name,
            point_count=len(point_rows),
            extended_count=len(extended_rows),
            queried=queried,
            matched=sum(1 for row in matches if row.gaia_match),
            error=error,
        )
        return GaiaVerificationResponse(
            status="completed",
            source_name=prepared.source_name,
            match_radius_arcsec=prepared.match_config.match_radius_arcsec,
            probability_power=prepared.match_config.probability_power,
            wcs_present=prepared.wcs is not None,
            queried=queried,
            error=error,
            summary=GaiaVerificationSummarySchema(
                point=self._summary_for(point_rows),
                extended=self._summary_for(extended_rows),
            ),
            matches=matches,
        )

    @staticmethod
    def _entries(
        point_sources: list[PointSource],
        extended_sources: list[ExtendedSource],
        wcs: WCS | None,
    ) -> list[_SourceEntry]:
        entries: list[_SourceEntry] = []
        if wcs is None:
            entries.extend(
                _SourceEntry(source.source_id, "point", source.rank, None)
                for source in point_sources
            )
            entries.extend(
                _SourceEntry(source.source_id, "extended", source.rank, None)
                for source in extended_sources
            )
            return entries
        entries.extend(
            _SourceEntry(
                source.source_id,
                "point",
                source.rank,
                to_sky(wcs, source.xcentroid, source.ycentroid),
            )
            for source in point_sources
        )
        entries.extend(
            _SourceEntry(
                source.source_id,
                "extended",
                source.rank,
                to_sky(wcs, source.xcentroid, source.ycentroid),
            )
            for source in extended_sources
        )
        return entries

    @staticmethod
    def _summary_for(rows: list[GaiaMatchSchema]) -> GaiaTypeSummarySchema:
        matched_count = sum(1 for row in rows if row.gaia_match)
        separations = [
            row.gaia_separation_arcsec
            for row in rows
            if row.gaia_match and row.gaia_separation_arcsec is not None
        ]
        median = float(np.median(separations)) if separations else None
        match_rate = matched_count / len(rows) if rows else 0.0
        return GaiaTypeSummarySchema(
            count=len(rows),
            matched=matched_count,
            match_rate=match_rate,
            median_separation_arcsec=median,
        )


__all__ = ["GaiaVerificationService"]
