from __future__ import annotations

import numpy as np
import pytest

from astroimage.sources.detection.background import estimate_background
from astroimage.sources.detection.extended import detect_extended_sources
from tests.unit.sources.helpers import synthetic_extended_source_image


def test_detects_extended_region_model_end_to_end() -> None:
    image, _ = synthetic_extended_source_image()
    background = estimate_background(image)

    detected = detect_extended_sources(image, background_rms=background.background_rms)

    assert len(detected) >= 1
    top = detected.iloc[0]
    assert 100.0 < top["xcentroid"] < 156.0
    assert 100.0 < top["ycentroid"] < 156.0
    assert top["width_pixels"] >= 64.0
    assert top["height_pixels"] >= 64.0
    assert top["area_pixels"] >= 2000
    assert 0.0 <= top["relevance_score"] <= 1.0


def test_score_columns_are_finite_and_ranked() -> None:
    image, _ = synthetic_extended_source_image()
    background = estimate_background(image)

    detected = detect_extended_sources(image, background_rms=background.background_rms)

    assert len(detected) >= 1
    assert np.isfinite(detected["relevance_score"]).all()
    assert np.isfinite(detected["peak"]).all()
    assert np.isfinite(detected["mean"]).all()
    assert np.isfinite(detected["flux"]).all()
    assert (detected["area_pixels"] > 0).all()
    assert detected["relevance_score"].is_monotonic_decreasing


def test_noise_only_image_returns_empty_frame() -> None:
    rng = np.random.default_rng(3)
    image = rng.normal(scale=5.0, size=(256, 256))

    detected = detect_extended_sources(image)

    assert len(detected) == 0


def test_empty_nan_image_returns_empty_frame() -> None:
    image = np.full((128, 128), np.nan)

    detected = detect_extended_sources(image)

    assert len(detected) == 0


def test_non_2d_image_raises() -> None:
    image = np.zeros((8, 8, 8))

    with pytest.raises(ValueError, match="2D"):
        detect_extended_sources(image)
