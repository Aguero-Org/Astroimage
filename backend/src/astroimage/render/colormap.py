from __future__ import annotations

from collections.abc import Callable

import numpy as np

from astroimage.render.schema import ColormapType

_LUT_SIZE = 256


def _greyscale_lut(inverted: bool = False) -> np.ndarray:
    intensity = np.linspace(0.0, 1.0, _LUT_SIZE)
    if inverted:
        intensity = 1.0 - intensity
    channels: np.ndarray = np.stack([intensity, intensity, intensity], axis=1)
    return channels


def _heat_lut() -> np.ndarray:
    intensity = np.linspace(0.0, 1.0, _LUT_SIZE)
    red = intensity
    green = np.clip(2.0 * intensity - 1.0, 0.0, 1.0)
    blue = np.clip(4.0 * intensity - 3.0, 0.0, 1.0)
    channels: np.ndarray = np.stack([red, green, blue], axis=1)
    return channels


def _rainbow_lut() -> np.ndarray:
    intensity = np.linspace(0.0, 1.0, _LUT_SIZE)
    hue = 240.0 * (1.0 - intensity)
    segment = np.floor(hue / 60.0).astype(int) % 6
    chroma = 1.0
    cross_component = chroma * (1.0 - np.abs(np.mod(hue / 60.0, 2.0) - 1.0))

    red = np.select(
        [
            segment == 0,
            segment == 1,
            segment == 2,
            segment == 3,
            segment == 4,
            segment == 5,
        ],
        [chroma, cross_component, 0.0, 0.0, cross_component, chroma],
    )
    green = np.select(
        [
            segment == 0,
            segment == 1,
            segment == 2,
            segment == 3,
            segment == 4,
            segment == 5,
        ],
        [cross_component, chroma, chroma, cross_component, 0.0, 0.0],
    )
    blue = np.select(
        [
            segment == 0,
            segment == 1,
            segment == 2,
            segment == 3,
            segment == 4,
            segment == 5,
        ],
        [0.0, 0.0, cross_component, chroma, chroma, cross_component],
    )
    channels: np.ndarray = np.stack([red, green, blue], axis=1)
    return channels


def _cube_helix_lut() -> np.ndarray:
    intensity = np.linspace(0.0, 1.0, _LUT_SIZE)
    value = intensity
    hue = 1.0
    amplitude = hue * value * (1.0 - value) / 2.0
    phase = 2.0 * np.pi * (0.5 / 3.0 + (-1.5) * value)

    red = value + amplitude * (-0.14861 * np.cos(phase) + 1.78277 * np.sin(phase))
    green = value + amplitude * (-0.29227 * np.cos(phase) - 0.06049 * np.sin(phase))
    blue = value + amplitude * (1.97294 * np.cos(phase) - 0.93648 * np.sin(phase))
    channels_raw: np.ndarray = np.stack([red, green, blue], axis=1)
    channels: np.ndarray = np.clip(channels_raw, 0.0, 1.0)
    return channels


_BUILDERS: dict[str, Callable[[], np.ndarray]] = {
    "grey": lambda: _greyscale_lut(inverted=False),
    "inverse": lambda: _greyscale_lut(inverted=True),
    "heat": _heat_lut,
    "rainbow": _rainbow_lut,
    "cube_helix": _cube_helix_lut,
}


def _build_luts() -> dict[str, np.ndarray]:
    luts: dict[str, np.ndarray] = {}
    for name, builder in _BUILDERS.items():
        channels: np.ndarray = builder()
        scaled: np.ndarray = np.round(channels * 255.0).astype(np.uint8)
        luts[name] = scaled
    return luts


COLORMAPS: dict[str, np.ndarray] = _build_luts()


def apply_colormap(frame: np.ndarray, colormap: ColormapType) -> np.ndarray:
    lut = COLORMAPS[colormap]
    indices: np.ndarray = frame.astype(np.intp)
    colored: np.ndarray = lut[indices]
    return colored
