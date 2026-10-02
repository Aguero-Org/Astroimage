"""Turn measured image statistics into detection parameters.

``fwhm`` is a physical property of the point spread function, not a taste
setting, so it is measured from the sources themselves with second moments.
Every other parameter the user can express intent with is kept, and only the
ones that describe the PSF scale are rescaled by the measured ratio.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from astroimage.sources.model import PointSource
from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    PointDetectionConfigSchema,
)

FWHM_PER_SIGMA = 2.3548200450309493

# First pass only needs to find the core; the stamp then grows to cover the
# measured width, otherwise the truncated tails bias the width downwards.
ROUGH_STAMP_RADIUS_PIXELS = 6
FWHM_RADIUS_SIGMAS = 4.5
MIN_STAMP_RADIUS_PIXELS = 6
MAX_STAMP_RADIUS_PIXELS = 36
MAX_RADIUS_REFINEMENTS = 4

MAX_SAMPLES = 25
MIN_SAMPLES = 3
MIN_SOURCE_SNR = 5.0
MIN_POSITIVE_PIXELS = 6
SATURATION_RATIO = 1.8

MIN_FWHM_PIXELS = 1.0
MAX_FWHM_FRACTION = 0.25

MAX_VISUAL_RADIUS_CAP = 32.0
MAX_SMOOTH_SIGMA = 64.0

MAD_TO_SIGMA = 1.4826


@dataclass(frozen=True)
class PsfMeasurement:
    fwhm: float | None
    samples: int
    spread: float | None = None

    @property
    def reliable(self) -> bool:
        return self.fwhm is not None and self.samples >= MIN_SAMPLES


@dataclass(frozen=True)
class PresetChange:
    parameter: str
    baseline: float
    recommended: float
    reason: str


@dataclass(frozen=True)
class PresetRecommendation:
    point_config: PointDetectionConfigSchema
    extended_config: ExtendedDetectionConfigSchema
    changes: list[PresetChange] = field(default_factory=list)


def _clamp(value: float, low: float, high: float) -> float:
    return float(min(max(value, low), high))


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _moments(
    image: np.ndarray,
    center_x: float,
    center_y: float,
    radius: int,
) -> tuple[float, float, float] | None:
    """Total flux, width in pixels and peak of one source inside a circular stamp."""
    height, width = image.shape
    x0, x1 = max(0, int(center_x) - radius), min(width, int(center_x) + radius + 1)
    y0, y1 = max(0, int(center_y) - radius), min(height, int(center_y) + radius + 1)
    patch = image[y0:y1, x0:x1]
    if patch.size == 0:
        return None

    work = np.asarray(patch, dtype=float) - np.median(patch)
    work = np.where(np.isfinite(work), work, 0.0)

    adj_y, adj_x = np.mgrid[y0:y1, x0:x1]
    inside = ((adj_x - center_x) ** 2 + (adj_y - center_y) ** 2) <= radius**2
    weights = np.where(inside, np.clip(work, 0.0, None), 0.0)

    total = float(weights.sum())
    if total <= 0 or int(np.count_nonzero(weights)) < MIN_POSITIVE_PIXELS:
        return None

    centroid_x = float((weights * adj_x).sum() / total)
    centroid_y = float((weights * adj_y).sum() / total)
    variance_x = float((weights * (adj_x - centroid_x) ** 2).sum() / total)
    variance_y = float((weights * (adj_y - centroid_y) ** 2).sum() / total)
    sigma_pixels = float(np.sqrt(max((variance_x + variance_y) / 2.0, 0.0)))
    if not np.isfinite(sigma_pixels) or sigma_pixels <= 0:
        return None

    return total, sigma_pixels, float(weights.max())


def _is_saturated(total: float, peak: float, sigma_pixels: float) -> bool:
    """Flat-topped sources are saturated cores or defects, not a usable PSF.

    A Gaussian whose total flux is ``total`` and width ``sigma_pixels`` peaks at
    ``total / (2 * pi * sigma**2)``. A core that is flat spreads the same flux
    over more pixels, so its observed peak sits well above that prediction.
    """
    expected_peak = total / (2.0 * np.pi * sigma_pixels**2)
    if expected_peak <= 0:
        return False
    return peak > SATURATION_RATIO * expected_peak


def _source_fwhm(image: np.ndarray, center_x: float, center_y: float) -> float | None:
    moments = _moments(image, center_x, center_y, ROUGH_STAMP_RADIUS_PIXELS)
    if moments is None:
        return None

    radius = ROUGH_STAMP_RADIUS_PIXELS
    for _ in range(MAX_RADIUS_REFINEMENTS):
        wanted = int(
            np.clip(
                np.ceil(FWHM_RADIUS_SIGMAS * moments[1]),
                MIN_STAMP_RADIUS_PIXELS,
                MAX_STAMP_RADIUS_PIXELS,
            )
        )
        if wanted == radius:
            break
        radius = wanted
        refined = _moments(image, center_x, center_y, radius)
        if refined is None:
            return None
        moments = refined

    total, sigma_pixels, peak = moments
    if _is_saturated(total, peak, sigma_pixels):
        return None
    return float(FWHM_PER_SIGMA * sigma_pixels)


def measure_psf_fwhm(
    data_sub: np.ndarray,
    sources: list[PointSource],
) -> PsfMeasurement:
    """Median FWHM over the brightest isolated sources of an image."""
    image = np.asarray(data_sub, dtype=float)
    if image.ndim != 2 or image.size == 0:
        return PsfMeasurement(fwhm=None, samples=0)
    max_fwhm = MAX_FWHM_FRACTION * float(min(image.shape))
    if max_fwhm <= MIN_FWHM_PIXELS:
        return PsfMeasurement(fwhm=None, samples=0)

    ordered = sorted(
        (source for source in sources if source.snr >= MIN_SOURCE_SNR),
        key=lambda source: source.snr,
        reverse=True,
    )
    measured: list[float] = []
    for source in ordered[:MAX_SAMPLES]:
        value = _source_fwhm(image, source.xcentroid, source.ycentroid)
        if value is None:
            continue
        if not MIN_FWHM_PIXELS <= value <= max_fwhm:
            continue
        measured.append(value)

    if not measured:
        return PsfMeasurement(fwhm=None, samples=0)

    median_fwhm = float(np.median(measured))
    median_absolute_deviation = float(np.median(np.abs(np.asarray(measured) - median_fwhm)))
    return PsfMeasurement(
        fwhm=_clamp(median_fwhm, MIN_FWHM_PIXELS, max_fwhm),
        samples=len(measured),
        spread=round(median_absolute_deviation * MAD_TO_SIGMA, 3),
    )


def _changed(
    changes: list[PresetChange], parameter: str, baseline: float, recommended: float, reason: str
) -> None:
    if _round(baseline, 3) != _round(recommended, 3):
        changes.append(
            PresetChange(
                parameter=parameter,
                baseline=_round(baseline, 3),
                recommended=_round(recommended, 3),
                reason=reason,
            )
        )


def derive_preset(
    *,
    measurement: PsfMeasurement,
    baseline_point: PointDetectionConfigSchema,
    baseline_extended: ExtendedDetectionConfigSchema,
) -> PresetRecommendation:
    """Rescale the PSF-dependent parameters, keep the rest of the user's intent."""
    if not measurement.reliable or measurement.fwhm is None:
        return PresetRecommendation(
            point_config=baseline_point,
            extended_config=baseline_extended,
        )

    fwhm = measurement.fwhm
    ratio = fwhm / baseline_point.fwhm
    changes: list[PresetChange] = []

    fwhm_text = f"FWHM measured on {measurement.samples} sources"
    _changed(changes, "fwhm", baseline_point.fwhm, fwhm, fwhm_text)

    min_distance = _clamp(baseline_point.min_distance * ratio, 0.0, fwhm)
    _changed(
        changes,
        "min_distance",
        baseline_point.min_distance,
        min_distance,
        "rescaled with fwhm to keep the same separation in PSF units",
    )

    visual_radius = _clamp(
        baseline_point.visual_area_radius * ratio,
        1.0,
        MAX_VISUAL_RADIUS_CAP,
    )
    _changed(
        changes,
        "visual_area_radius",
        baseline_point.visual_area_radius,
        visual_radius,
        "rescaled with fwhm so the aperture still covers the same PSF",
    )

    smooth_sigma = _clamp(baseline_extended.smooth_sigma * ratio, 0.5, MAX_SMOOTH_SIGMA)
    _changed(
        changes,
        "smooth_sigma",
        baseline_extended.smooth_sigma,
        smooth_sigma,
        "rescaled with fwhm to keep the smoothing kernel at the same PSF scale",
    )

    min_area = max(1, round(baseline_extended.min_area * ratio**2))
    _changed(
        changes,
        "min_area",
        float(baseline_extended.min_area),
        float(min_area),
        "rescaled with the square of fwhm to keep the same area in PSF units",
    )

    return PresetRecommendation(
        point_config=baseline_point.model_copy(
            update={"fwhm": fwhm, "min_distance": min_distance, "visual_area_radius": visual_radius}
        ),
        extended_config=baseline_extended.model_copy(
            update={"smooth_sigma": smooth_sigma, "min_area": min_area}
        ),
        changes=changes,
    )


def median_source_snr(sources: list[PointSource]) -> float | None:
    values = [source.snr for source in sources if np.isfinite(source.snr)]
    if not values:
        return None
    return round(float(np.median(np.asarray(values, dtype=float))), 3)
