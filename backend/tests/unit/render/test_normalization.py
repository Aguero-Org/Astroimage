from __future__ import annotations

import numpy as np

from astroimage.render.normalization import normalize_to_uint8


def test_sqrt_stretch_maps_data_to_full_range() -> None:
    data = np.linspace(0.0, 100.0, 64).reshape(8, 8)

    frame = normalize_to_uint8(data, stretch="sqrt", pmin=0.0, pmax=100.0, gamma=1.0)

    assert frame.dtype == np.uint8
    assert frame.shape == (8, 8)
    assert frame.min() == 0
    assert frame.max() == 255
    assert (np.diff(frame.flatten()) >= 0).all()


def test_log_and_asinh_stretches_are_monotonic() -> None:
    data = np.linspace(0.0, 200.0, 128).reshape(8, 16)

    for stretch in ("log", "asinh"):
        frame = normalize_to_uint8(data, stretch=stretch, pmin=0.0, pmax=100.0, gamma=1.0)
        assert frame.dtype == np.uint8
        assert frame.min() == 0
        assert frame.max() == 255
        assert (np.diff(frame.flatten()) >= 0).all()


def test_nan_and_infinite_pixels_render_black() -> None:
    data = np.linspace(0.0, 100.0, 16).reshape(4, 4)
    data[0, 0] = np.nan
    data[1, 1] = np.inf
    data[2, 2] = -np.inf

    frame = normalize_to_uint8(data, stretch="sqrt", pmin=0.0, pmax=100.0, gamma=1.0)

    assert np.all(np.isfinite(frame))
    assert frame[0, 0] == 0
    assert frame[1, 1] == 0
    assert frame[2, 2] == 0


def test_constant_image_renders_mid_gray() -> None:
    data = np.full((4, 4), 42.0)

    frame = normalize_to_uint8(data, stretch="sqrt", pmin=1.0, pmax=99.0, gamma=1.0)

    assert (frame == 128).all()


def test_all_nan_image_renders_black() -> None:
    data = np.full((4, 4), np.nan)

    frame = normalize_to_uint8(data, stretch="sqrt", pmin=1.0, pmax=99.0, gamma=1.0)

    assert (frame == 0).all()


def test_outliers_are_clipped_by_percentiles() -> None:
    data = np.linspace(0.0, 255.0, 64).reshape(8, 8)
    data[7, 7] = 1.0e9

    frame = normalize_to_uint8(data, stretch="sqrt", pmin=1.0, pmax=99.0, gamma=1.0)

    assert np.all(np.isfinite(frame))
    assert frame.max() == 255
    assert frame[7, 7] == 255
