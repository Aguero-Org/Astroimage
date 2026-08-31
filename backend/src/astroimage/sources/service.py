from __future__ import annotations

import math

import pandas as pd

from astroimage.fits.reader import FitsReader
from astroimage.sources.detection.background import estimate_background
from astroimage.sources.detection.filtering import select_point_sources
from astroimage.sources.detection.point import detect_point_sources
from astroimage.sources.model import PointSource, SourceDetectionResult
from astroimage.sources.schema import (
    DetectionSummarySchema,
    ExtendedSourceSchema,
    PointDetectionConfigSchema,
    PointSourceSchema,
    SourceDetectionResponse,
)


def _optional_float(value: float | None) -> float | None:
    if value is None:
        return None
    converted = float(value)
    if not math.isfinite(converted):
        return None
    return converted


class SourceDetectionService:
    def __init__(self, reader: FitsReader | None = None) -> None:
        self._reader = reader or FitsReader()

    def detect(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
        config: PointDetectionConfigSchema | None = None,
    ) -> SourceDetectionResult:
        detection_config = config or PointDetectionConfigSchema()
        image = self._reader.read_image_data_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )
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
        return SourceDetectionResult(
            source_name=image.source_name,
            point_sources=self._to_point_sources(selected),
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
