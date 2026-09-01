from __future__ import annotations

import io

import numpy as np
from astropy.io import fits


def synthetic_point_source_image(
    size: int = 256,
    *,
    background_level: float = 0.0,
    noise_sigma: float = 8.0,
    peak: float = 5000.0,
    fwhm: float = 5.0,
    seed: int = 7,
    positions: tuple[tuple[float, float], ...] = (
        (60.5, 70.5),
        (150.5, 40.5),
        (190.5, 180.5),
    ),
) -> tuple[np.ndarray, np.ndarray]:
    coordinates = np.mgrid[0:size, 0:size]
    rng = np.random.default_rng(seed)
    image = background_level + rng.normal(scale=noise_sigma, size=(size, size))
    noise = rng.normal(scale=noise_sigma, size=(size, size))
    sigma = fwhm / 2.3548
    for coordinate_x, coordinate_y in positions:
        distance_sq = (coordinates[1] - coordinate_x) ** 2 + (coordinates[0] - coordinate_y) ** 2
        image = image + peak * np.exp(-distance_sq / (2.0 * sigma**2))
    return image, noise


def fits_bytes_from_image(image: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()
