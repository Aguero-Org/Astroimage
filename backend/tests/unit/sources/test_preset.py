from __future__ import annotations

import numpy as np
import pytest

from astroimage.sources.detection.preset import (
    FWHM_PER_SIGMA,
    MAX_SAMPLES,
    MIN_SAMPLES,
    PresetChange,
    PsfMeasurement,
    derive_preset,
    measure_psf_fwhm,
    median_source_snr,
)
from astroimage.sources.model import PointSource
from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    PointDetectionConfigSchema,
)

# Spaced far beyond the stamp radius so each measurement sees only its own source.
GRID = [
    (30.0, 30.0),
    (100.0, 30.0),
    (170.0, 30.0),
    (30.0, 100.0),
    (100.0, 100.0),
    (170.0, 100.0),
    (30.0, 170.0),
    (100.0, 170.0),
    (170.0, 170.0),
]


def gaussian_image(
    shape: tuple[int, int],
    positions: list[tuple[float, float]],
    fwhm: float,
    *,
    amplitude: float = 1000.0,
) -> np.ndarray:
    height, width = shape
    adj_y, adj_x = np.mgrid[0:height, 0:width]
    sigma = fwhm / FWHM_PER_SIGMA
    image = np.zeros(shape)
    for center_x, center_y in positions:
        image += amplitude * np.exp(
            -((adj_x - center_x) ** 2 + (adj_y - center_y) ** 2) / (2.0 * sigma**2)
        )
    return image


def point_source(x: float, y: float, snr: float = 40.0) -> PointSource:
    return PointSource(
        source_id=1,
        rank=1,
        xcentroid=x,
        ycentroid=y,
        snr=snr,
        relevance_score=0.9,
    )


@pytest.mark.parametrize("fwhm", [2.0, 3.5, 5.5, 9.0])
def test_measured_fwhm_matches_the_synthetic_psf(fwhm: float) -> None:
    image = gaussian_image((220, 220), GRID, fwhm)

    measurement = measure_psf_fwhm(image, [point_source(x, y) for x, y in GRID])

    assert measurement.reliable
    assert measurement.samples == len(GRID)
    assert measurement.fwhm == pytest.approx(fwhm, rel=0.05)


def test_measurement_reports_spread_for_uneven_sources() -> None:
    widths = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
    image = np.zeros((420, 420))
    sources: list[PointSource] = []
    for center, width in zip(GRID, widths, strict=True):
        image += gaussian_image((420, 420), [center], width)
        sources.append(point_source(*center))

    measurement = measure_psf_fwhm(image, sources)

    assert measurement.reliable
    assert measurement.samples == len(GRID)
    assert measurement.spread is not None
    assert measurement.spread > 1.0


def test_measurement_of_uniform_sources_has_no_spread() -> None:
    image = gaussian_image((220, 220), GRID, 4.0)

    measurement = measure_psf_fwhm(image, [point_source(x, y) for x, y in GRID])

    assert measurement.reliable
    assert measurement.spread == pytest.approx(0.0, abs=1e-6)


def test_measurement_ignores_faint_sources() -> None:
    image = gaussian_image((220, 220), GRID, 4.0)

    assert not measure_psf_fwhm(image, [point_source(60.0, 60.0, snr=1.0)]).reliable


def test_measurement_needs_enough_sources() -> None:
    image = gaussian_image((220, 220), [(100.0, 100.0)], 4.0)

    measurement = measure_psf_fwhm(image, [point_source(100.0, 100.0)])

    assert measurement.samples == 1
    assert not measurement.reliable


def test_measurement_uses_at_most_the_brightest_sources() -> None:
    crowded = [(float(x), float(y)) for y in range(40, 400, 30) for x in range(40, 400, 30)]
    assert len(crowded) > MAX_SAMPLES
    image = gaussian_image((420, 420), crowded, 4.0)
    sources = [
        point_source(x, y, snr=snr)
        for (x, y), snr in zip(crowded, range(1, len(crowded) + 1), strict=True)
    ]

    measurement = measure_psf_fwhm(image, sources)

    assert measurement.reliable
    assert measurement.samples == MAX_SAMPLES
    assert measurement.fwhm == pytest.approx(4.0, rel=0.1)


def test_measurement_skips_saturated_sources() -> None:
    image = gaussian_image((220, 220), GRID[1:], 4.0)
    image[24:36, 24:36] = 5000.0

    measurement = measure_psf_fwhm(
        image,
        [point_source(*GRID[0]), *[point_source(x, y) for x, y in GRID[1:]]],
    )

    assert measurement.reliable
    assert measurement.samples == len(GRID) - 1
    assert measurement.fwhm == pytest.approx(4.0, rel=0.1)


def test_measurement_returns_nothing_for_an_empty_image() -> None:
    measurement = measure_psf_fwhm(np.zeros((64, 64)), [])

    assert measurement.fwhm is None
    assert measurement.samples == 0
    assert not measurement.reliable


def test_measurement_rejects_sources_on_the_border() -> None:
    image = gaussian_image((220, 220), [(0.0, 0.0)], 4.0)

    assert not measure_psf_fwhm(image, [point_source(0.0, 0.0)]).reliable


def test_measurement_rejects_a_non_image() -> None:
    assert not measure_psf_fwhm(np.zeros((0, 0)), []).reliable


def test_measurement_rejects_images_too_small_to_hold_a_psf() -> None:
    assert not measure_psf_fwhm(np.zeros((12, 12)), [point_source(6.0, 6.0)]).reliable


def test_preset_rescales_the_psf_dependent_parameters() -> None:
    recommendation = derive_preset(
        measurement=PsfMeasurement(fwhm=11.0, samples=8, spread=0.2),
        baseline_point=PointDetectionConfigSchema(),
        baseline_extended=ExtendedDetectionConfigSchema(),
    )

    assert recommendation.point_config.fwhm == 11.0
    assert recommendation.point_config.min_distance == pytest.approx(8.0)
    assert recommendation.point_config.visual_area_radius == pytest.approx(14.0)
    assert recommendation.extended_config.smooth_sigma == pytest.approx(16.0)
    assert recommendation.extended_config.min_area == 500 * 4


def test_preset_keeps_the_parameters_that_are_not_psf_scale() -> None:
    baseline_point = PointDetectionConfigSchema(sigma=7.0, min_snr=11.0, min_score=0.42)
    baseline_extended = ExtendedDetectionConfigSchema(sigma=4.0, max_sources=9)

    recommendation = derive_preset(
        measurement=PsfMeasurement(fwhm=3.0, samples=6, spread=0.1),
        baseline_point=baseline_point,
        baseline_extended=baseline_extended,
    )

    assert recommendation.point_config.sigma == 7.0
    assert recommendation.point_config.min_snr == 11.0
    assert recommendation.point_config.min_score == 0.42
    assert recommendation.point_config.max_sources == baseline_point.max_sources
    assert recommendation.point_config.visual_weight == baseline_point.visual_weight
    assert recommendation.point_config.visual_area_sigma == baseline_point.visual_area_sigma
    assert recommendation.extended_config.sigma == 4.0
    assert recommendation.extended_config.max_sources == 9


def test_preset_respects_the_baseline_ratio_not_the_defaults() -> None:
    baseline_point = PointDetectionConfigSchema(fwhm=5.0, min_distance=1.0)

    recommendation = derive_preset(
        measurement=PsfMeasurement(fwhm=10.0, samples=6, spread=0.1),
        baseline_point=baseline_point,
        baseline_extended=ExtendedDetectionConfigSchema(),
    )

    assert recommendation.point_config.min_distance == pytest.approx(2.0)


def test_preset_returns_the_baseline_when_the_measurement_is_unusable() -> None:
    baseline_point = PointDetectionConfigSchema()
    baseline_extended = ExtendedDetectionConfigSchema()

    recommendation = derive_preset(
        measurement=PsfMeasurement(fwhm=None, samples=0),
        baseline_point=baseline_point,
        baseline_extended=baseline_extended,
    )

    assert recommendation.point_config is baseline_point
    assert recommendation.extended_config is baseline_extended
    assert recommendation.changes == []


def test_preset_needs_enough_samples_even_with_a_fwhm() -> None:
    baseline_point = PointDetectionConfigSchema()

    recommendation = derive_preset(
        measurement=PsfMeasurement(fwhm=9.0, samples=MIN_SAMPLES - 1),
        baseline_point=baseline_point,
        baseline_extended=ExtendedDetectionConfigSchema(),
    )

    assert recommendation.point_config is baseline_point


def test_preset_reports_every_changed_parameter() -> None:
    recommendation = derive_preset(
        measurement=PsfMeasurement(fwhm=11.0, samples=8),
        baseline_point=PointDetectionConfigSchema(),
        baseline_extended=ExtendedDetectionConfigSchema(),
    )

    reported = {change.parameter for change in recommendation.changes}
    assert reported == {
        "fwhm",
        "min_distance",
        "visual_area_radius",
        "smooth_sigma",
        "min_area",
    }
    assert all(change.reason for change in recommendation.changes)


def test_preset_does_not_report_unchanged_parameters() -> None:
    recommendation = derive_preset(
        measurement=PsfMeasurement(fwhm=5.5, samples=8),
        baseline_point=PointDetectionConfigSchema(),
        baseline_extended=ExtendedDetectionConfigSchema(),
    )

    assert recommendation.changes == []
    assert recommendation.point_config == PointDetectionConfigSchema()


def test_preset_caps_the_aperture_and_the_smoothing() -> None:
    recommendation = derive_preset(
        measurement=PsfMeasurement(fwhm=200.0, samples=8),
        baseline_point=PointDetectionConfigSchema(),
        baseline_extended=ExtendedDetectionConfigSchema(),
    )

    assert recommendation.point_config.visual_area_radius <= 32.0
    assert recommendation.extended_config.smooth_sigma <= 64.0
    assert recommendation.point_config.min_distance <= 200.0


def test_preset_min_area_stays_a_positive_integer() -> None:
    recommendation = derive_preset(
        measurement=PsfMeasurement(fwhm=0.6, samples=8),
        baseline_point=PointDetectionConfigSchema(),
        baseline_extended=ExtendedDetectionConfigSchema(min_area=4),
    )

    assert recommendation.extended_config.min_area >= 1


def test_preset_change_keeps_its_fields() -> None:
    change = PresetChange(parameter="fwhm", baseline=5.5, recommended=9.0, reason="measured")

    assert change.parameter == "fwhm"
    assert change.baseline == 5.5
    assert change.recommended == 9.0
    assert change.reason == "measured"


def test_median_snr_of_the_detected_sources() -> None:
    sources = [
        point_source(1.0, 1.0, snr=10.0),
        point_source(2.0, 2.0, snr=20.0),
        point_source(3.0, 3.0, snr=30.0),
    ]

    assert median_source_snr(sources) == 20.0


def test_median_snr_without_sources() -> None:
    assert median_source_snr([]) is None
