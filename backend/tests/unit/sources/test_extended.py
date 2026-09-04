from __future__ import annotations

import numpy as np

from astroimage.sources.detection.extended import detect_extended_sources

_SIZE = 600
_CENTER_X = 300.0
_CENTER_Y = 300.0


def _diffuse_blob_image(
    center_x: float = _CENTER_X,
    center_y: float = _CENTER_Y,
    *,
    peak: float = 12000.0,
    width: float = 40.0,
    background_level: float = 0.0,
    noise_sigma: float = 8.0,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(7)
    image = background_level + rng.normal(scale=noise_sigma, size=(_SIZE, _SIZE))
    coordinate_y, coordinate_x = np.mgrid[0:_SIZE, 0:_SIZE]
    bivariate = ((coordinate_x - center_x) / width) ** 2 + ((coordinate_y - center_y) / width) ** 2
    image = image + peak * np.exp(-0.5 * bivariate)
    noise = np.full_like(image, noise_sigma)
    return image, noise


def test_extended_blob_detected_at_center() -> None:
    image, noise = _diffuse_blob_image()

    extended_result = detect_extended_sources(
        image,
        noise,
        sigma=6.0,
        min_snr=0.0,
        max_sources=20,
    )

    assert len(extended_result) == 1
    near = extended_result[
        (np.abs(extended_result["xcentroid"] - _CENTER_X) < 30.0)
        & (np.abs(extended_result["ycentroid"] - _CENTER_Y) < 30.0)
    ]
    assert len(near) == 1
    assert extended_result["object_type"].iloc[0] == "extended"
    assert extended_result["rank"].tolist() == [1]
    assert extended_result["source_id"].tolist() == [1]


def test_extended_min_snr_filters_low_snr_regions() -> None:
    image, noise = _diffuse_blob_image()

    detected = detect_extended_sources(
        image,
        noise,
        sigma=6.0,
        min_snr=0.0,
        max_sources=20,
    )
    detected_snr = float(detected["snr"].iloc[0])

    filtered = detect_extended_sources(
        image,
        noise,
        sigma=6.0,
        min_snr=detected_snr * 10.0,
        max_sources=20,
    )
    assert len(filtered) == 0


def test_extended_max_sources_limits_regions() -> None:
    image, noise = _diffuse_blob_image()

    limited = detect_extended_sources(
        image,
        noise,
        sigma=6.0,
        min_snr=0.0,
        max_sources=10,
    )
    assert len(limited) <= 10


def test_extended_noise_only_returns_empty() -> None:
    rng = np.random.default_rng(4)
    image = rng.normal(scale=8.0, size=(128, 128))
    noise = np.full_like(image, 8.0)

    extended_result = detect_extended_sources(
        image,
        noise,
        sigma=6.0,
        min_snr=0.0,
        max_sources=10,
    )

    assert len(extended_result) == 0


def test_extended_empty_without_diffuse_blob() -> None:
    rng = np.random.default_rng(7)
    image = rng.normal(scale=8.0, size=(_SIZE, _SIZE))
    noise = np.full_like(image, 8.0)
    coordinate_y, coordinate_x = np.mgrid[0:_SIZE, 0:_SIZE]
    sigma = 2.0
    for coordinate_x_pos, coordinate_y_pos in ((60.5, 70.5), (150.5, 40.5), (190.5, 180.5)):
        distance_sq = (coordinate_x - coordinate_x_pos) ** 2 + (
            coordinate_y - coordinate_y_pos
        ) ** 2
        image = image + 300.0 * np.exp(-distance_sq / (2.0 * sigma**2))

    extended_result = detect_extended_sources(
        image,
        noise,
        sigma=6.0,
        min_snr=0.0,
        max_sources=20,
    )

    assert len(extended_result) == 0


def test_extended_blob_near_border_is_penalized_not_ranked_first() -> None:
    rng = np.random.default_rng(7)
    image = rng.normal(scale=8.0, size=(_SIZE, _SIZE))
    noise = np.full_like(image, 8.0)
    coordinate_y, coordinate_x = np.mgrid[0:_SIZE, 0:_SIZE]
    for center_x, center_y in ((_CENTER_X, _CENTER_Y), (65.0, 70.0)):
        bivariate = ((coordinate_x - center_x) / 30.0) ** 2 + (
            (coordinate_y - center_y) / 30.0
        ) ** 2
        image = image + 12000.0 * np.exp(-0.5 * bivariate)

    result = detect_extended_sources(
        image,
        noise,
        sigma=6.0,
        min_snr=0.0,
        max_sources=20,
    )

    assert len(result) == 2
    center_near = result[
        (np.abs(result["xcentroid"] - _CENTER_X) < 30.0)
        & (np.abs(result["ycentroid"] - _CENTER_Y) < 30.0)
    ]
    border_near = result[
        (np.abs(result["xcentroid"] - 65.0) < 30.0) & (np.abs(result["ycentroid"] - 70.0) < 30.0)
    ]
    assert len(center_near) == 1
    assert len(border_near) == 1
    assert int(center_near["rank"].iloc[0]) < int(border_near["rank"].iloc[0])
