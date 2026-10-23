from __future__ import annotations

import math
import time
from uuid import UUID

import numpy as np
import pandas as pd
import structlog
from opentelemetry import trace

from astroimage.fits.reader import FitsReader
from astroimage.fits.service import FitsService
from astroimage.sources.cache import (
    CachedDetection,
    DetectionCache,
    detection_cache_key,
    detection_scope_key,
)
from astroimage.sources.detection.background import estimate_background
from astroimage.sources.detection.extended import detect_extended_sources
from astroimage.sources.detection.filtering import (
    select_extended_sources,
    select_point_sources,
)
from astroimage.sources.detection.point import detect_point_sources
from astroimage.sources.detection.preset import (
    derive_preset,
    measure_psf_fwhm,
    median_source_snr,
)
from astroimage.sources.model import ExtendedSource, PointSource, SourceDetectionResult
from astroimage.sources.schema import (
    DetectionSummarySchema,
    ExtendedDetectionConfigSchema,
    ExtendedSourceSchema,
    PointDetectionConfigSchema,
    PointSourceSchema,
    PresetChangeSchema,
    PresetEvidenceSchema,
    SourceDetectionResponse,
    SourcePresetResponse,
)

FITS_SERVICE_NOT_CONFIGURED = "FitsService not configured"

_log = structlog.get_logger("astroimage.sources.detection")
_tracer = trace.get_tracer("astroimage.sources.detection")


def _analysis_matches(metadata_payload: object, hdu_index: int | None) -> bool:
    if not isinstance(metadata_payload, dict) or "image" not in metadata_payload:
        return False
    hdus = metadata_payload.get("hdus")
    if not isinstance(hdus, dict):
        return False
    selected = hdus.get("selected")
    if not isinstance(selected, int):
        return False
    if hdu_index is None:
        return True
    return selected == hdu_index


def _optional_float(value: float | None) -> float | None:
    if value is None:
        return None
    converted = float(value)
    if not math.isfinite(converted):
        return None
    return converted


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
            raise RuntimeError(FITS_SERVICE_NOT_CONFIGURED)
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
            return cached.result
        record = await self._fits.get_record(record_id)
        payload = await self._fits.get_payload(record)
        if not _analysis_matches(record.metadata_payload, hdu_index):
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
        self._cache.set(
            key,
            CachedDetection(
                result=result,
                point_config=detection_config,
                extended_config=extended_detection_config,
            ),
            scope=detection_scope_key(
                record_id=record_id,
                client_id=client_id,
                hdu_index=hdu_index,
            ),
        )
        return result

    async def recommend_preset(
        self,
        record_id: UUID,
        *,
        client_id: str = "anonymous",
        hdu_index: int | None = None,
    ) -> SourcePresetResponse:
        """Measure the PSF on this image and rescale the parameters that follow it.

        Reuses the last detection this client ran on the image when there is one,
        otherwise runs the default detection to get sources to measure.
        """
        if self._fits is None:
            raise RuntimeError(FITS_SERVICE_NOT_CONFIGURED)
        scope = detection_scope_key(
            record_id=record_id,
            client_id=client_id,
            hdu_index=hdu_index,
        )
        cached = self._cache.get_latest(scope)
        from_cache = cached is not None
        if cached is None:
            cached = CachedDetection(
                result=await self.resolve_detection_from_record(
                    record_id,
                    client_id=client_id,
                    hdu_index=hdu_index,
                ),
                point_config=PointDetectionConfigSchema(),
                extended_config=ExtendedDetectionConfigSchema(),
            )

        record = await self._fits.get_record(record_id)
        payload = await self._fits.get_payload(record)
        image = self._reader.read_image_data_from_bytes(
            payload,
            source_name=record.original_filename,
            hdu_index=hdu_index,
        )
        background = estimate_background(image.data)
        measurement = measure_psf_fwhm(
            background.data_sub,
            cached.result.point_sources,
        )
        recommendation = derive_preset(
            measurement=measurement,
            baseline_point=cached.point_config,
            baseline_extended=cached.extended_config,
        )
        _log.info(
            "preset_recommended",
            record_id=str(record_id),
            client_id=client_id,
            from_cache=from_cache,
            measured_fwhm=measurement.fwhm,
            fwhm_samples=measurement.samples,
            recommended_fwhm=recommendation.point_config.fwhm,
            changes=len(recommendation.changes),
        )
        return SourcePresetResponse(
            point_config=recommendation.point_config,
            extended_config=recommendation.extended_config,
            baseline_point_config=cached.point_config,
            baseline_extended_config=cached.extended_config,
            evidence=PresetEvidenceSchema(
                measured_fwhm=measurement.fwhm,
                fwhm_samples=measurement.samples,
                fwhm_spread=measurement.spread,
                background_rms=float(np.nanmedian(background.background_rms)),
                point_count=len(cached.result.point_sources),
                extended_count=len(cached.result.extended_sources),
                median_snr=median_source_snr(cached.result.point_sources),
                from_cache=from_cache,
            ),
            changes=[
                PresetChangeSchema(
                    parameter=change.parameter,
                    baseline=change.baseline,
                    recommended=change.recommended,
                    reason=change.reason,
                )
                for change in recommendation.changes
            ],
        )

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


__all__ = ["FITS_SERVICE_NOT_CONFIGURED", "SourceDetectionService"]
