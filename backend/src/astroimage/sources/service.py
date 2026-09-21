from __future__ import annotations

import math
import time
from uuid import UUID

import pandas as pd
import structlog
from opentelemetry import trace

from astroimage.fits.reader import FitsReader
from astroimage.fits.service import FitsService
from astroimage.sources.detection.background import estimate_background
from astroimage.sources.detection.extended import detect_extended_sources
from astroimage.sources.detection.filtering import (
    select_extended_sources,
    select_point_sources,
)
from astroimage.sources.detection.point import detect_point_sources
from astroimage.sources.model import ExtendedSource, PointSource, SourceDetectionResult
from astroimage.sources.schema import (
    DetectionSummarySchema,
    ExtendedDetectionConfigSchema,
    ExtendedSourceSchema,
    PointDetectionConfigSchema,
    PointSourceSchema,
    SourceDetectionResponse,
)

_log = structlog.get_logger("astroimage.sources.service")
_tracer = trace.get_tracer("astroimage.sources.service")


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
    ) -> None:
        self._reader = reader or FitsReader()
        self._fits = fits

    async def detect_from_record(
        self,
        record_id: UUID,
        *,
        hdu_index: int | None = None,
        config: PointDetectionConfigSchema | None = None,
        extended_config: ExtendedDetectionConfigSchema | None = None,
    ) -> SourceDetectionResult:
        if self._fits is None:
            raise RuntimeError("FitsService not configured")
        record = await self._fits.get_record(record_id)
        payload = await self._fits.get_payload(record)
        _log.info(
            "metadata_analysis_start",
            record_id=str(record_id),
            payload_bytes=len(payload),
        )
        await self._fits.update_record_metadata(record, payload, hdu_index=hdu_index)
        _log.debug("detect_running", record_id=str(record_id))
        return self.detect(
            payload,
            source_name=record.original_filename,
            hdu_index=hdu_index,
            config=config,
            extended_config=extended_config,
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

    def to_schema(self, result: SourceDetectionResult) -> SourceDetectionResponse:
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
        )
