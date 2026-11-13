from __future__ import annotations

from typing import Annotated

from fastapi import Query

from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    PointDetectionConfigSchema,
)

_DEFAULTS = PointDetectionConfigSchema()
_EXTENDED_DEFAULTS = ExtendedDetectionConfigSchema()

FwhmParam = Annotated[float, Query(ge=0.5)]
SigmaParam = Annotated[float, Query(ge=1.0)]
MinSnrParam = Annotated[float, Query(ge=0.0)]
MinScoreParam = Annotated[float, Query(ge=0.0, le=1.0)]
MinDistanceParam = Annotated[float, Query(ge=0.0)]
VisualWeightParam = Annotated[float, Query(ge=0.0, le=1.0)]
VisualAreaRadiusParam = Annotated[float, Query(ge=1.0)]
VisualAreaSigmaParam = Annotated[float, Query(ge=0.0)]
MaxSourcesParam = Annotated[int, Query(ge=0)]
ExtendedSigmaParam = Annotated[float, Query(ge=0.5)]
ExtendedSmoothSigmaParam = Annotated[float, Query(ge=0.5)]
ExtendedMinAreaParam = Annotated[int, Query(ge=1)]
ExtendedMaxAreaParam = Annotated[int, Query(ge=0)]
ExtendedBinFactorParam = Annotated[int, Query(ge=1)]
ExtendedClosingIterationsParam = Annotated[int, Query(ge=0)]
ExtendedOpeningIterationsParam = Annotated[int, Query(ge=0)]
ExtendedMinScoreParam = Annotated[float, Query(ge=0.0, le=1.0)]
ExtendedMaxSourcesParam = Annotated[int, Query(ge=0)]


def _config(
    fwhm: float,
    sigma: float,
    min_snr: float,
    min_score: float,
    min_distance: float,
    visual_weight: float,
    visual_area_radius: float,
    visual_area_sigma: float,
    max_sources: int,
) -> PointDetectionConfigSchema:
    return PointDetectionConfigSchema(
        fwhm=fwhm,
        sigma=sigma,
        min_snr=min_snr,
        min_score=min_score,
        min_distance=min_distance,
        visual_weight=visual_weight,
        visual_area_radius=visual_area_radius,
        visual_area_sigma=visual_area_sigma,
        max_sources=max_sources,
    )


def _extended_config(
    ext_sigma: float,
    ext_smooth_sigma: float,
    ext_min_area: int,
    ext_max_area: int,
    ext_bin_factor: int,
    ext_closing_iterations: int,
    ext_opening_iterations: int,
    ext_min_score: float,
    ext_max_sources: int,
) -> ExtendedDetectionConfigSchema:
    return ExtendedDetectionConfigSchema(
        sigma=ext_sigma,
        smooth_sigma=ext_smooth_sigma,
        min_area=ext_min_area,
        max_area=ext_max_area,
        bin_factor=ext_bin_factor,
        closing_iterations=ext_closing_iterations,
        opening_iterations=ext_opening_iterations,
        min_score=ext_min_score,
        max_sources=ext_max_sources,
    )


def point_detection_query(
    fwhm: FwhmParam = _DEFAULTS.fwhm,
    sigma: SigmaParam = _DEFAULTS.sigma,
    min_snr: MinSnrParam = _DEFAULTS.min_snr,
    min_score: MinScoreParam = _DEFAULTS.min_score,
    min_distance: MinDistanceParam = _DEFAULTS.min_distance,
    visual_weight: VisualWeightParam = _DEFAULTS.visual_weight,
    visual_area_radius: VisualAreaRadiusParam = _DEFAULTS.visual_area_radius,
    visual_area_sigma: VisualAreaSigmaParam = _DEFAULTS.visual_area_sigma,
    max_sources: MaxSourcesParam = _DEFAULTS.max_sources,
) -> PointDetectionConfigSchema:
    return _config(
        fwhm,
        sigma,
        min_snr,
        min_score,
        min_distance,
        visual_weight,
        visual_area_radius,
        visual_area_sigma,
        max_sources,
    )


def extended_detection_query(
    ext_sigma: ExtendedSigmaParam = _EXTENDED_DEFAULTS.sigma,
    ext_smooth_sigma: ExtendedSmoothSigmaParam = _EXTENDED_DEFAULTS.smooth_sigma,
    ext_min_area: ExtendedMinAreaParam = _EXTENDED_DEFAULTS.min_area,
    ext_max_area: ExtendedMaxAreaParam = _EXTENDED_DEFAULTS.max_area,
    ext_bin_factor: ExtendedBinFactorParam = _EXTENDED_DEFAULTS.bin_factor,
    ext_closing_iterations: ExtendedClosingIterationsParam = (
        _EXTENDED_DEFAULTS.closing_iterations
    ),
    ext_opening_iterations: ExtendedOpeningIterationsParam = (
        _EXTENDED_DEFAULTS.opening_iterations
    ),
    ext_min_score: ExtendedMinScoreParam = _EXTENDED_DEFAULTS.min_score,
    ext_max_sources: ExtendedMaxSourcesParam = _EXTENDED_DEFAULTS.max_sources,
) -> ExtendedDetectionConfigSchema:
    return _extended_config(
        ext_sigma,
        ext_smooth_sigma,
        ext_min_area,
        ext_max_area,
        ext_bin_factor,
        ext_closing_iterations,
        ext_opening_iterations,
        ext_min_score,
        ext_max_sources,
    )
