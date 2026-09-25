from __future__ import annotations

import asyncio
import math
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

import astropy.units as u
import numpy as np
import pandas as pd
import structlog
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning
from opentelemetry import trace

from astroimage.fits.reader import FitsMetadata, FitsReader
from astroimage.fits.service import FitsService
from astroimage.sources.cache import DetectionCache, detection_cache_key
from astroimage.sources.detection.background import estimate_background
from astroimage.sources.detection.extended import detect_extended_sources
from astroimage.sources.detection.filtering import (
    select_extended_sources,
    select_point_sources,
)
from astroimage.sources.detection.point import detect_point_sources
from astroimage.sources.gaia import (
    AstroqueryGaiaProvider,
    GaiaCatalogProvider,
    GaiaObject,
    GaiaSourceMatch,
    match_sources_to_gaia,
    search_radius_arcsec,
)
from astroimage.sources.model import ExtendedSource, PointSource, SourceDetectionResult
from astroimage.sources.schema import (
    DetectionSummarySchema,
    ExtendedDetectionConfigSchema,
    ExtendedSourceSchema,
    GaiaMatchConfigSchema,
    GaiaMatchSchema,
    GaiaTypeSummarySchema,
    GaiaVerificationResponse,
    GaiaVerificationSummarySchema,
    PointDetectionConfigSchema,
    PointSourceSchema,
    SourceDetectionResponse,
)

_log = structlog.get_logger("astroimage.sources.service")
_FITS_SERVICE_NOT_CONFIGURED = "FitsService not configured"
_tracer = trace.get_tracer("astroimage.sources.service")
_GAIA_QUERY_TIMEOUT_S = 120.0
_GAIA_CONCURRENCY = 8
_gaia_executor = ThreadPoolExecutor(
    max_workers=_GAIA_CONCURRENCY,
    thread_name_prefix="gaia",
)


def _optional_float(value: float | None) -> float | None:
    if value is None:
        return None
    converted = float(value)
    if not math.isfinite(converted):
        return None
    return converted


@dataclass(frozen=True)
class _SourceEntry:
    source_id: int
    object_type: Literal["point", "extended"]
    rank: int
    coordinate: SkyCoord | None


def _world_coordinates(metadata: FitsMetadata) -> WCS | None:
    if not metadata.wcs.present:
        return None
    header = fits.Header()
    for key, value in metadata.header.items():
        header[key] = value
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FITSFixedWarning)
        return WCS(header, naxis=2, relax=True)


def _to_sky(wcs: WCS, coordinate_x: float, coordinate_y: float) -> SkyCoord:
    world = wcs.pixel_to_world(coordinate_x, coordinate_y)
    return SkyCoord(
        ra=float(world.ra.deg) * u.deg,
        dec=float(world.dec.deg) * u.deg,
        frame="icrs",
    )


def _field_center(detected_coords: list[SkyCoord]) -> SkyCoord:
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
        center = _field_center(chunk)
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


class SourceDetectionService:
    def __init__(
        self,
        reader: FitsReader | None = None,
        fits: FitsService | None = None,
        cache: DetectionCache | None = None,
    ) -> None:
        self._reader = reader or FitsReader()
        self._fits = fits
        self._cache = cache or DetectionCache()

    async def detect_from_record(
        self,
        record_id: UUID,
        *,
        client_id: str = "anonymous",
        hdu_index: int | None = None,
        config: PointDetectionConfigSchema | None = None,
        extended_config: ExtendedDetectionConfigSchema | None = None,
    ) -> SourceDetectionResult:
        return await self.resolve_detection_from_record(
            record_id,
            client_id=client_id,
            hdu_index=hdu_index,
            config=config,
            extended_config=extended_config,
        )

    async def resolve_detection_from_record(
        self,
        record_id: UUID,
        *,
        client_id: str = "anonymous",
        hdu_index: int | None = None,
        config: PointDetectionConfigSchema | None = None,
        extended_config: ExtendedDetectionConfigSchema | None = None,
    ) -> SourceDetectionResult:
        if self._fits is None:
            raise RuntimeError(_FITS_SERVICE_NOT_CONFIGURED)
        detection_config = config or PointDetectionConfigSchema()
        extended_detection_config = extended_config or ExtendedDetectionConfigSchema()
        key = detection_cache_key(
            record_id=record_id,
            client_id=client_id,
            hdu_index=hdu_index,
            config=detection_config,
            extended_config=extended_detection_config,
        )
        cached = self._cache.get(key)
        if cached is not None:
            _log.info(
                "detection_cache_hit",
                record_id=str(record_id),
                client_id=client_id,
            )
            return cached
        record = await self._fits.get_record(record_id)
        payload = await self._fits.get_payload(record)
        _log.info(
            "metadata_analysis_start",
            record_id=str(record_id),
            payload_bytes=len(payload),
        )
        await self._fits.update_record_metadata(record, payload, hdu_index=hdu_index)
        _log.debug("detect_running", record_id=str(record_id))
        result = self.detect(
            payload,
            source_name=record.original_filename,
            hdu_index=hdu_index,
            config=detection_config,
            extended_config=extended_detection_config,
        )
        self._cache.set(key, result)
        return result

    def detect(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
        config: PointDetectionConfigSchema | None = None,
        extended_config: ExtendedDetectionConfigSchema | None = None,
    ) -> SourceDetectionResult:
        with _tracer.start_as_current_span("source_detection") as span:
            detection_config = config or PointDetectionConfigSchema()
            extended_detection_config = extended_config or ExtendedDetectionConfigSchema()
            read_start = time.perf_counter()
            image = self._reader.read_image_data_from_bytes(
                payload,
                source_name=source_name,
                hdu_index=hdu_index,
            )
            read_ms = round((time.perf_counter() - read_start) * 1000, 2)
            span.set_attribute("source_name", source_name or "unknown")
            span.set_attribute("image_hdu_index", image.hdu_index)

            detect_start = time.perf_counter()
            background = estimate_background(image.data)
            candidates = detect_point_sources(
                background.data_sub,
                background.background_rms,
                fwhm=detection_config.fwhm,
                sigma=detection_config.sigma,
                min_distance=detection_config.min_distance,
                visual_area_radius=detection_config.visual_area_radius,
                visual_area_sigma=detection_config.visual_area_sigma,
                visual_weight=detection_config.visual_weight,
            )
            selected = select_point_sources(
                candidates,
                min_snr=detection_config.min_snr,
                min_score=detection_config.min_score,
                max_sources=detection_config.max_sources,
            )
            extended_candidates = detect_extended_sources(
                image.data,
                background_rms=background.background_rms,
                sigma=extended_detection_config.sigma,
                smooth_sigma=extended_detection_config.smooth_sigma,
                min_area=extended_detection_config.min_area,
                bin_factor=extended_detection_config.bin_factor,
                max_area=extended_detection_config.max_area or None,
                closing_iterations=extended_detection_config.closing_iterations,
                opening_iterations=extended_detection_config.opening_iterations,
            )
            selected_extended = select_extended_sources(
                extended_candidates,
                min_score=extended_detection_config.min_score,
                max_sources=extended_detection_config.max_sources,
            )
            detect_ms = round((time.perf_counter() - detect_start) * 1000, 2)
            sources = self._to_point_sources(selected)
            extended_sources = self._to_extended_sources(selected_extended)
            span.set_attribute("point_source_count", len(sources))
            span.set_attribute("extended_source_count", len(extended_sources))
            _log.info(
                "detect_step_complete",
                source_name=source_name,
                point_count=len(sources),
                extended_count=len(extended_sources),
                read_ms=read_ms,
                detect_ms=detect_ms,
            )
            return SourceDetectionResult(
                source_name=image.source_name,
                point_sources=sources,
                extended_sources=extended_sources,
            )

    def _to_point_sources(self, frame: pd.DataFrame | None) -> list[PointSource]:
        if frame is None or len(frame) == 0:
            return []
        sources: list[PointSource] = []
        for _, row in frame.iterrows():
            sources.append(
                PointSource(
                    source_id=int(row["source_id"]),
                    rank=int(row["rank"]),
                    xcentroid=float(row["xcentroid"]),
                    ycentroid=float(row["ycentroid"]),
                    snr=float(row["snr"]),
                    relevance_score=float(row["relevance_score"]),
                    peak=_optional_float(row.get("peak")),
                    flux=_optional_float(row.get("flux")),
                )
            )
        return sources

    def _to_extended_sources(self, frame: pd.DataFrame | None) -> list[ExtendedSource]:
        if frame is None or len(frame) == 0:
            return []
        sources: list[ExtendedSource] = []
        for _, row in frame.iterrows():
            sources.append(
                ExtendedSource(
                    source_id=int(row["source_id"]),
                    rank=int(row["rank"]),
                    xcentroid=float(row["xcentroid"]),
                    ycentroid=float(row["ycentroid"]),
                    width_pixels=float(row["width_pixels"]),
                    height_pixels=float(row["height_pixels"]),
                    area_pixels=int(row["area_pixels"]),
                    peak=float(row["peak"]),
                    mean=float(row["mean"]),
                    flux=float(row["flux"]),
                    relevance_score=float(row["relevance_score"]),
                )
            )
        return sources

    def to_schema(
        self,
        result: SourceDetectionResult,
        *,
        gaia_url: str | None = None,
    ) -> SourceDetectionResponse:
        return SourceDetectionResponse(
            source_name=result.source_name,
            summary=DetectionSummarySchema(
                point_count=len(result.point_sources),
                extended_count=len(result.extended_sources),
            ),
            point_sources=[
                PointSourceSchema.model_validate(source.model_dump())
                for source in result.point_sources
            ],
            extended_sources=[
                ExtendedSourceSchema.model_validate(source.model_dump())
                for source in result.extended_sources
            ],
            gaia_url=gaia_url,
        )


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
            raise RuntimeError(_FITS_SERVICE_NOT_CONFIGURED)
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
            raise RuntimeError(_FITS_SERVICE_NOT_CONFIGURED)
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
            # Fallback single-query (paridad con TPI-Prueba, gaia.py:183-204):
            # si todos los bloques devuelven vac\u00edo, reintentamos sobre el
            # campo completo para evitar falsos negativos en campos densos.
            _log.info("gaia_fallback_triggered", record_id=str(record_id))
            fallback_center = _field_center(prepared.entry_coords)
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
            except Exception as exc:
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
                center = _field_center(prepared.entry_coords)
                radius = search_radius_arcsec(
                    center,
                    prepared.entry_coords,
                    match_radius_arcsec=prepared.match_config.match_radius_arcsec,
                )
                try:
                    objects = self.provider.search_cone(center, radius)
                except Exception as exc:
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
        wcs = _world_coordinates(metadata)
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
                _to_sky(wcs, source.xcentroid, source.ycentroid),
            )
            for source in point_sources
        )
        entries.extend(
            _SourceEntry(
                source.source_id,
                "extended",
                source.rank,
                _to_sky(wcs, source.xcentroid, source.ycentroid),
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
