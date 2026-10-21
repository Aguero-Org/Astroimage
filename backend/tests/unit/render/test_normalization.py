from __future__ import annotations

from typing import cast

import numpy as np
import pytest

from astroimage.render.normalization import _apply_stretch, normalize_to_uint8
from astroimage.render.schema import StretchType


def test_sqrt_stretch_maps_data_to_full_range() -> None:
    data = np.linspace(0.0, 100.0, 64).reshape(8, 8)

    frame = normalize_to_uint8(
        data,
        stretch="sqrt",
        limits="percentiles",
        pmin=0.0,
        pmax=100.0,
        gamma=1.0,
    )

    assert frame.dtype == np.uint8
    assert frame.shape == (8, 8)
    assert frame.min() == 0
    assert frame.max() == 255
    assert (np.diff(frame.flatten()) >= 0).all()


def test_linear_stretch_maps_data_to_full_range() -> None:
    data = np.linspace(0.0, 100.0, 64).reshape(8, 8)

    frame = normalize_to_uint8(
        data,
        stretch="linear",
        limits="percentiles",
        pmin=0.0,
        pmax=100.0,
        gamma=1.0,
    )

    assert frame.dtype == np.uint8
    assert frame.min() == 0
    assert frame.max() == 255
    assert (np.diff(frame.flatten()) >= 0).all()


def test_log_and_asinh_stretches_are_monotonic() -> None:
    data = np.linspace(0.0, 200.0, 128).reshape(8, 16)

    for stretch in ("log", "asinh"):
        frame = normalize_to_uint8(
            data,
            stretch=stretch,
            limits="percentiles",
            pmin=0.0,
            pmax=100.0,
            gamma=1.0,
        )
        assert frame.dtype == np.uint8
        assert frame.min() == 0
        assert frame.max() == 255
        assert (np.diff(frame.flatten()) >= 0).all()


def test_zscale_limits_keep_data_visible() -> None:
    rng = np.random.default_rng(seed=5)
    data = rng.normal(loc=50.0, scale=10.0, size=(64, 64))
    data[0, 0] = 1.0e6
    data[1, 0] = -1.0e6

    frame = normalize_to_uint8(
        data,
        stretch="sqrt",
        limits="zscale",
        pmin=1.0,
        pmax=99.0,
        gamma=1.0,
    )

    assert frame.dtype == np.uint8
    assert frame.shape == (64, 64)
    assert np.all(np.isfinite(frame))
    assert frame.min() == 0
    assert frame.max() == 255
    assert frame[0, 0] == 255
    assert frame[1, 0] == 0


def test_nan_and_infinite_pixels_render_black() -> None:
    data = np.linspace(0.0, 100.0, 16).reshape(4, 4)
    data[0, 0] = np.nan
    data[1, 1] = np.inf
    data[2, 2] = -np.inf

    frame = normalize_to_uint8(
        data,
        stretch="sqrt",
        limits="percentiles",
        pmin=0.0,
        pmax=100.0,
        gamma=1.0,
    )

    assert np.all(np.isfinite(frame))
    assert frame[0, 0] == 0
    assert frame[1, 1] == 0
    assert frame[2, 2] == 0


def test_constant_image_renders_mid_gray() -> None:
    data = np.full((4, 4), 42.0)

    frame = normalize_to_uint8(
        data,
        stretch="sqrt",
        limits="percentiles",
        pmin=1.0,
        pmax=99.0,
        gamma=1.0,
    )

    assert frame.dtype == np.uint8
    assert (frame == 128).all()


def test_all_nan_image_renders_black() -> None:
    data = np.full((4, 4), np.nan)

    frame = normalize_to_uint8(
        data,
        stretch="sqrt",
        limits="percentiles",
        pmin=1.0,
        pmax=99.0,
        gamma=1.0,
    )

    assert frame.dtype == np.uint8
    assert (frame == 0).all()


def test_outliers_are_clipped_by_percentiles() -> None:
    data = np.linspace(0.0, 255.0, 64).reshape(8, 8)
    data[7, 7] = 1.0e9

    frame = normalize_to_uint8(
        data,
        stretch="sqrt",
        limits="percentiles",
        pmin=1.0,
        pmax=99.0,
        gamma=1.0,
    )

    assert np.all(np.isfinite(frame))
    assert frame.max() == 255
    assert frame[7, 7] == 255


def test_stretch_formulas_match_reference() -> None:
    values = np.array([0.0, 0.25, 0.5, 1.0])

    assert np.allclose(
        _apply_stretch(values, "log"),
        np.log1p(999.0 * values) / np.log1p(999.0),
    )
    assert np.allclose(
        _apply_stretch(values, "asinh"),
        np.arcsinh(200.0 * values) / np.arcsinh(200.0),
    )


def test_unknown_stretch_names_the_value() -> None:
    with pytest.raises(ValueError, match="Unknown stretch: bogus"):
        normalize_to_uint8(
            np.arange(4.0).reshape(2, 2),
            stretch=cast(StretchType, "bogus"),
            limits="percentiles",
            pmin=0.0,
            pmax=100.0,
            gamma=1.0,
        )


def test_zscale_limits_widen_constant_image() -> None:
    data = np.full((4, 4), 42.0)

    frame = normalize_to_uint8(
        data,
        stretch="sqrt",
        limits="zscale",
        pmin=0.0,
        pmax=100.0,
        gamma=1.0,
    )

    assert frame.dtype == np.uint8
    assert (frame == 180).all()


def test_gamma_uses_inverse_power() -> None:
    data = np.array([[0.0, 0.25, 0.5, 0.75, 1.0]])

    frame = normalize_to_uint8(
        data,
        stretch="linear",
        limits="percentiles",
        pmin=0.0,
        pmax=100.0,
        gamma=2.0,
    )

    expected = np.round(np.sqrt(data) * 255.0).astype(np.uint8)
    assert np.array_equal(frame, expected)


def test_percentile_scaling_uses_display_width() -> None:
    data = np.linspace(10.0, 19.0, 10).reshape(2, 5)

    frame = normalize_to_uint8(
        data,
        stretch="linear",
        limits="percentiles",
        pmin=0.0,
        pmax=100.0,
        gamma=1.0,
    )

    assert frame.min() == 0
    assert frame.max() == 255


def test_lower_values_are_clipped_before_stretch() -> None:
    data = np.arange(10.0).reshape(2, 5)

    frame = normalize_to_uint8(
        data,
        stretch="linear",
        limits="percentiles",
        pmin=50.0,
        pmax=100.0,
        gamma=1.0,
    )

    assert (frame.flatten()[:5] == 0).all()
    assert frame.max() == 255


def test_nonfinite_values_are_zeroed_before_stretch() -> None:
    data = np.array([[0.0, 100.0, np.nan, np.inf, -np.inf]])

    frame = normalize_to_uint8(
        data,
        stretch="linear",
        limits="percentiles",
        pmin=0.0,
        pmax=100.0,
        gamma=1.0,
    )

    assert np.array_equal(frame, np.array([[0, 255, 0, 0, 0]], dtype=np.uint8))
