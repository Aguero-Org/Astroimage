from __future__ import annotations

import numpy as np
import pytest

from astroimage.sources.detection.point import detect_point_sources
from tests.unit.sources.helpers import synthetic_point_source_image


def test_detects_injected_sources_near_real_positions() -> None:
    image, noise = synthetic_point_source_image()
    expected = ((60.5, 70.5), (150.5, 40.5), (190.5, 180.5))

    detected = detect_point_sources(
        image,
        noise,
        fwhm=5.0,
        sigma=6.0,
        min_distance=6.0,
    )

    assert len(detected) >= 3
    for expected_x, expected_y in expected:
        match = detected[
            (np.abs(detected["xcentroid"] - expected_x) < 3.0)
            & (np.abs(detected["ycentroid"] - expected_y) < 3.0)
        ]
        assert len(match) == 1, f"faltó la fuente en ({expected_x}, {expected_y})"


def test_score_columns_are_finite_and_ranked() -> None:
    image, noise = synthetic_point_source_image()

    detected = detect_point_sources(
        image,
        noise,
        fwhm=5.0,
        sigma=6.0,
        min_distance=6.0,
    )

    assert len(detected) >= 1
    assert np.isfinite(detected["snr"]).all()
    assert np.isfinite(detected["relevance_score"]).all()
    assert detected["rank"].tolist() == list(range(1, len(detected) + 1))
    assert detected["point_source"].all()
    assert detected["relevance_score"].is_monotonic_decreasing


def test_constant_image_returns_empty_frame() -> None:
    image = np.zeros((128, 128))
    noise = np.full((128, 128), 5.0)

    detected = detect_point_sources(image, noise, fwhm=5.0, sigma=6.0)

    assert len(detected) == 0


def test_invalid_background_rms_raises() -> None:
    image, _ = synthetic_point_source_image()

    with pytest.raises(ValueError, match="RMS"):
        detect_point_sources(image, np.full((256, 256), 0.0))
