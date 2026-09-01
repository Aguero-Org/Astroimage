from __future__ import annotations

import numpy as np
import pytest

from astroimage.render.zscale import zscale_bounds


def test_zscale_bounds_on_noise_without_outliers() -> None:
    rng = np.random.default_rng(seed=11)
    image = rng.normal(scale=5.0, size=(64, 64))

    low, high = zscale_bounds(image)

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
