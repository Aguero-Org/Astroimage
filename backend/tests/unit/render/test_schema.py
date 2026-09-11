from __future__ import annotations

import pytest
from pydantic import ValidationError

from astroimage.render.schema import RenderConfigSchema


def test_defaults() -> None:
    config = RenderConfigSchema()
    assert config.stretch == "sqrt"
    assert config.limits == "percentiles"
    assert config.colormap == "grey"
    assert config.pmin == 1.0
    assert config.pmax == 99.0
    assert config.gamma == 1.0


def test_pmin_must_be_lower_than_pmax() -> None:
    with pytest.raises(ValidationError, match="pmin"):
        RenderConfigSchema(pmin=50.0, pmax=20.0)


def test_extra_fields_are_forbidden() -> None:
    with pytest.raises(ValidationError):
        RenderConfigSchema.model_validate({"stretch": "log", "brightness": 2.0})
