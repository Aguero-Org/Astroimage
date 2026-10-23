from __future__ import annotations

import numpy as np
import pytest

from astroimage.render.zscale import (
    _compute_sigma,
    _fit_line,
    _sample_pixels,
    _window_sum,
    zscale_bounds,
)


def test_zscale_bounds_on_noise_without_outliers() -> None:
    rng = np.random.default_rng(seed=11)
    image = rng.normal(scale=5.0, size=(64, 64))

    low, high = zscale_bounds(image)

    assert low == pytest.approx(-15.74304615360861)
    assert high == pytest.approx(16.409034469678126)
    assert low < high
    assert np.isfinite(low) and np.isfinite(high)
    assert low <= float(np.median(image)) <= high
    assert -20.0 < low < high < 20.0


def test_zscale_bounds_ignores_outlier_pixels() -> None:
    rng = np.random.default_rng(seed=3)
    image = rng.normal(scale=1.0, size=(128, 128))
    image[0, 0] = 1.0e6
    image[1, 0] = -1.0e6

    low, high = zscale_bounds(image)

    assert low == pytest.approx(-3.0134517552232745)
    assert high == pytest.approx(6.1765745693971965)
    assert low < high
    assert -10.0 < low < high < 10.0


def test_zscale_bounds_with_bright_source() -> None:
    image = np.full((100, 100), 100.0)
    image[50:60, 50:60] = 5000.0

    low, high = zscale_bounds(image)

    assert low < high
    assert low >= 90.0
    assert high <= 600.0


def test_zscale_bounds_constant_image_widens_limits() -> None:
    image = np.full((16, 16), 42.0)

    low, high = zscale_bounds(image)

    assert low == pytest.approx(41.5)
    assert high == pytest.approx(42.5)


def test_zscale_bounds_all_nan_returns_unit_range() -> None:
    image = np.full((16, 16), np.nan)

    low, high = zscale_bounds(image)

    assert (low, high) == (0.0, 1.0)


def test_zscale_bounds_non_2d_raises() -> None:
    with pytest.raises(ValueError, match="2D"):
        zscale_bounds(np.zeros((4, 4, 4)))


def test_zscale_bounds_supports_single_pixel_image() -> None:
    low, high = zscale_bounds(np.array([[42.0]]))

    assert (low, high) == (42.0, 42.0)


def test_zscale_bounds_uses_minimum_sample_count_threshold() -> None:
    image = np.array([[0.0], [1.0], [1.0], [1.0], [1.0]])

    low, high = zscale_bounds(image)

    assert low == pytest.approx(0.2)
    assert high == pytest.approx(1.0)


def test_zscale_bounds_handles_odd_sample_count() -> None:
    rng = np.random.default_rng(seed=7)
    image = rng.normal(scale=3.0, size=(63, 63))

    low, high = zscale_bounds(image)

    assert low == pytest.approx(-8.473482060713794)
    assert high == pytest.approx(9.45086358471372)


def test_sample_pixels_respects_max_pixels() -> None:
    image = np.arange(25.0).reshape(5, 5)

    samples = _sample_pixels(image, max_pixels=3)

    assert samples.size == 3


def test_compute_sigma_returns_zero_for_fewer_than_two_pixels() -> None:
    assert _compute_sigma(np.array([]), np.array([], dtype=bool)) == 0.0
    assert _compute_sigma(np.array([5.0]), np.array([True])) == 0.0


def test_compute_sigma_uses_sample_standard_deviation() -> None:
    residuals = np.array([1.0, 3.0, 5.0])
    good_pixels = np.ones(residuals.size, dtype=bool)

    sigma = _compute_sigma(residuals, good_pixels)

    assert sigma == pytest.approx(float(np.std(residuals, ddof=1)))

    pair = np.array([1.0, 3.0])
    assert _compute_sigma(pair, np.ones(pair.size, dtype=bool)) == pytest.approx(
        float(np.std(pair, ddof=1))
    )


def test_sample_pixels_uses_square_root_stride() -> None:
    image = np.arange(52.0).reshape(2, 26)

    samples = _sample_pixels(image, max_pixels=3)

    assert np.array_equal(samples, np.array([0.0, 2.0, 4.0]))


def test_zscale_bounds_uses_two_middle_values_for_even_sample_count() -> None:
    image = np.array(
        [
            [-20.113343063411623],
            [3.8702335159766923],
            [4.845340839939385],
            [6.437747362907515],
            [6.570712723243113],
            [8.208955370771104],
            [8.259833406843134],
            [10.458580282677438],
        ]
    )

    low, high = zscale_bounds(image)

    assert low == pytest.approx(-16.94103394071387)
    assert high == pytest.approx(10.458580282677438)


def test_zscale_bounds_uses_single_pixel_growth_for_small_samples() -> None:
    rng = np.random.default_rng(seed=0)
    image = rng.normal(scale=3.0, size=(10, 8))
    image.flat[[5, 23, 61]] += 50.0

    low, high = zscale_bounds(image)

    assert low == pytest.approx(-6.975092323916503)
    assert high == pytest.approx(41.04537728666037)


def test_window_sum_grows_rejected_pixels() -> None:
    bad_pixels = np.array([True, False, False, True, False, False, True])

    output = _window_sum(bad_pixels, window=6)

    assert np.array_equal(output, np.array([1, 2, 2, 2, 2, 2, 2]))
    assert np.issubdtype(output.dtype, np.integer)


def test_fit_line_recovers_linear_samples() -> None:
    samples = np.arange(10.0)

    good_count, offset, slope = _fit_line(
        samples,
        rejection=2.5,
        growth_window=1,
        max_iterations=5,
    )

    assert good_count == 10
    assert offset == pytest.approx(0.0)
    assert slope == pytest.approx(1.0)
