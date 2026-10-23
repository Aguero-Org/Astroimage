from __future__ import annotations

import numpy as np
import pytest

from astroimage.render.colormap import (
    _BUILDERS,
    COLORMAPS,
    _build_luts,
    _greyscale_lut,
    apply_colormap,
)

_NAMES = tuple(COLORMAPS.keys())


def _scale(channels: np.ndarray) -> np.ndarray:
    return np.round(channels * 255.0).astype(np.uint8)


def _reference_greyscale(inverted: bool) -> np.ndarray:
    intensity = np.linspace(0.0, 1.0, 256)
    if inverted:
        intensity = 1.0 - intensity
    return _scale(np.stack([intensity, intensity, intensity], axis=1))


def _reference_heat() -> np.ndarray:
    intensity = np.linspace(0.0, 1.0, 256)
    red = intensity
    green = np.clip(2.0 * intensity - 1.0, 0.0, 1.0)
    blue = np.clip(4.0 * intensity - 3.0, 0.0, 1.0)
    return _scale(np.stack([red, green, blue], axis=1))


def _reference_rainbow() -> np.ndarray:
    intensity = np.linspace(0.0, 1.0, 256)
    hue = 240.0 * (1.0 - intensity)
    segment = np.floor(hue / 60.0).astype(int) % 6
    cross = 1.0 * (1.0 - np.abs(np.mod(hue / 60.0, 2.0) - 1.0))
    conditions = [segment == index for index in range(6)]
    red = np.select(conditions, [1.0, cross, 0.0, 0.0, cross, 1.0])
    green = np.select(conditions, [cross, 1.0, 1.0, cross, 0.0, 0.0])
    blue = np.select(conditions, [0.0, 0.0, cross, 1.0, 1.0, cross])
    return _scale(np.stack([red, green, blue], axis=1))


def _reference_cube_helix() -> np.ndarray:
    value = np.linspace(0.0, 1.0, 256)
    amplitude = 1.0 * value * (1.0 - value) / 2.0
    phase = 2.0 * np.pi * (0.5 / 3.0 + (-1.5) * value)
    red = value + amplitude * (-0.14861 * np.cos(phase) + 1.78277 * np.sin(phase))
    green = value + amplitude * (-0.29227 * np.cos(phase) - 0.06049 * np.sin(phase))
    blue = value + amplitude * (1.97294 * np.cos(phase) - 0.93648 * np.sin(phase))
    channels = np.stack([red, green, blue], axis=1)
    return _scale(np.clip(channels, 0.0, 1.0))


def test_lut_builders_match_reference_formulas() -> None:
    assert np.array_equal(_scale(_BUILDERS["grey"]()), _reference_greyscale(False))
    assert np.array_equal(_scale(_BUILDERS["inverse"]()), _reference_greyscale(True))
    assert np.array_equal(_scale(_BUILDERS["heat"]()), _reference_heat())
    assert np.array_equal(_scale(_BUILDERS["rainbow"]()), _reference_rainbow())
    assert np.array_equal(_scale(_BUILDERS["cube_helix"]()), _reference_cube_helix())


def test_colormaps_are_the_scaled_builders() -> None:
    expected = {name: _scale(builder()) for name, builder in _BUILDERS.items()}

    assert set(COLORMAPS) == set(expected)
    for name, lut in expected.items():
        assert np.array_equal(COLORMAPS[name], lut)


def test_build_luts_scales_every_builder() -> None:
    luts = _build_luts()

    assert set(luts) == set(_BUILDERS)
    for name, builder in _BUILDERS.items():
        assert luts[name].dtype == np.uint8
        assert np.array_equal(luts[name], _scale(builder()))


def test_greyscale_lut_defaults_to_forward_intensity() -> None:
    assert np.array_equal(_scale(_greyscale_lut()), _reference_greyscale(False))


def test_colormaps_have_expected_shape_and_dtype() -> None:
    assert set(COLORMAPS) == {"grey", "inverse", "heat", "rainbow", "cube_helix"}
    for name, lut in COLORMAPS.items():
        assert lut.shape == (256, 3), name
        assert lut.dtype == np.uint8


@pytest.mark.parametrize("name", _NAMES)
def test_colormaps_are_finite(name: str) -> None:
    assert np.all(np.isfinite(COLORMAPS[name]))


def test_grey_and_inverse_are_opposites() -> None:
    assert (COLORMAPS["grey"][0] == (0, 0, 0)).all()
    assert (COLORMAPS["grey"][-1] == (255, 255, 255)).all()
    assert (COLORMAPS["inverse"][0] == (255, 255, 255)).all()
    assert (COLORMAPS["inverse"][-1] == (0, 0, 0)).all()


def test_heat_runs_black_to_white() -> None:
    heat = COLORMAPS["heat"]
    assert (heat[0] == (0, 0, 0)).all()
    assert (heat[-1] == (255, 255, 255)).all()
    assert len({tuple(row) for row in heat}) == 256


def test_rainbow_goes_blue_to_red() -> None:
    rainbow = COLORMAPS["rainbow"]
    low_channel = rainbow[0]
    high_channel = rainbow[-1]
    assert low_channel[2] >= 200 and low_channel[0] <= 50
    assert high_channel[0] >= 200 and high_channel[2] <= 50


def test_cube_helix_endpoints() -> None:
    cube_helix = COLORMAPS["cube_helix"]
    assert cube_helix[0][2] >= cube_helix[0][0]
    assert cube_helix[-1][0] >= cube_helix[-1][2]


def test_apply_colormap_maps_frame_to_rgb() -> None:
    frame = np.array([[0, 128, 255]], dtype=np.uint8)

    colored = apply_colormap(frame, "grey")

    assert colored.shape == (1, 3, 3)
    assert (colored[0, 0] == (0, 0, 0)).all()
    assert (colored[0, 1] == (128, 128, 128)).all()
    assert (colored[0, 2] == (255, 255, 255)).all()


def test_apply_colormap_unknown_name_raises() -> None:
    with pytest.raises(KeyError):
        apply_colormap(np.zeros((1, 1), dtype=np.uint8), "magma")  # type: ignore[arg-type]


@pytest.mark.parametrize("name", _NAMES)
def test_apply_colormap_maps_every_index(name: str) -> None:
    frame = np.arange(256, dtype=np.uint8).reshape(16, 16)

    colored = apply_colormap(frame, name)  # type: ignore[arg-type]

    assert np.array_equal(colored, COLORMAPS[name][frame])
