from __future__ import annotations

import numpy as np

from astroimage.render.schema import LimitsType, StretchType
from astroimage.render.zscale import zscale_bounds

_LOG_SCALE = 999.0
_ASINH_SCALE = 200.0


def _apply_stretch(values: np.ndarray, stretch: StretchType) -> np.ndarray:
    if stretch == "linear":
        values_linear: np.ndarray = values
        return values_linear
    if stretch == "sqrt":
        values_sqrt: np.ndarray = np.sqrt(values)
        return values_sqrt
    if stretch == "log":
        values_log: np.ndarray = np.log1p(_LOG_SCALE * values) / np.log1p(_LOG_SCALE)
        return values_log
    if stretch == "asinh":
        values_asinh: np.ndarray = np.arcsinh(_ASINH_SCALE * values) / np.arcsinh(_ASINH_SCALE)
        return values_asinh
    raise ValueError(f"Unknown stretch: {stretch}")


def _display_bounds(
    image: np.ndarray,
    finite: np.ndarray,
    limits: LimitsType,
    pmin: float,
    pmax: float,
) -> tuple[float, float]:
    if limits == "zscale":
        return zscale_bounds(image)
    low = float(np.percentile(finite, pmin))
    high = float(np.percentile(finite, pmax))
    return low, high


def normalize_to_uint8(
    data: np.ndarray,
    *,
    stretch: StretchType,
    limits: LimitsType,
    pmin: float,
    pmax: float,
    gamma: float,
) -> np.ndarray:
    original = np.asarray(data, dtype=float)
    finite = original[np.isfinite(original)]
    if finite.size == 0:
        return np.zeros(original.shape, dtype=np.uint8)

    low, high = _display_bounds(original, finite, limits, pmin, pmax)

    image = original.copy()
    if not np.all(np.isfinite(image)):
        image[~np.isfinite(image)] = 0.0

    if high <= low:
        return np.full(image.shape, 128, dtype=np.uint8)

    scaled = np.clip((image - low) / (high - low), 0.0, 1.0)
    stretched = _apply_stretch(scaled, stretch)
    gamma_corrected: np.ndarray = np.power(stretched, 1.0 / gamma)
    frame: np.ndarray = np.round(gamma_corrected * 255.0).astype(np.uint8)
    return frame
