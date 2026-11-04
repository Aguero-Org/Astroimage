from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from astroimage.render.spec import Colormap, Limits, Stretch


class RenderConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stretch: Stretch = "sqrt"
    limits: Limits = "percentiles"
    colormap: Colormap = "grey"
    pmin: float = Field(default=1.0, ge=0.0, lt=100.0)
    pmax: float = Field(default=99.0, gt=0.0, le=100.0)
    gamma: float = Field(default=1.0, ge=0.1, le=5.0)

    @model_validator(mode="after")
    def _validate_percentile_range(self) -> RenderConfigSchema:
        if self.pmin >= self.pmax:
            raise ValueError("pmin must be lower than pmax")
        return self


class HistogramResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bin_centers: list[float]
    counts: list[int]
    minimum: float
    maximum: float
