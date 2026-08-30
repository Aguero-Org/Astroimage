from __future__ import annotations

import numpy as np
import pytest

from astroimage.sources.detection.background import estimate_background


def test_background_subtracts_constant_and_reports_rms() -> None:
    rng = np.random.default_rng(42)
    image = 1000.0 + rng.normal(scale=10.0, size=(128, 128))

    model = estimate_background(image)

    assert model.data_sub.shape == image.shape
    assert model.background.shape == image.shape
    assert model.background_rms.shape == image.shape
    assert np.isfinite(model.data_sub).all()
    assert float(np.nanmedian(model.background_rms)) > 0.0


def test_background_median_like_level() -> None:
    rng = np.random.default_rng(1)
    image = 500.0 + rng.normal(scale=5.0, size=(128, 128))

    model = estimate_background(image)

    assert abs(float(np.nanmedian(model.background)) - 500.0) < 10.0


def test_all_nan_image_raises() -> None:
    image = np.full((64, 64), np.nan)

    with pytest.raises(ValueError, match="valores finitos"):
        estimate_background(image)
