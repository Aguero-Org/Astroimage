from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

StretchType = Literal["linear", "sqrt", "log", "asinh"]
LimitsType = Literal["percentiles", "zscale"]
ColormapType = Literal["grey", "inverse", "heat", "rainbow", "cube_helix"]


class RenderConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stretch: StretchType = "sqrt"
    limits: LimitsType = "percentiles"
    colormap: ColormapType = "grey"
    pmin: float = Field(default=1.0, ge=0.0, lt=100.0)
    pmax: float = Field(default=99.0, gt=0.0, le=100.0)
    gamma: float = Field(default=1.0, ge=0.1, le=5.0)

    @model_validator(mode="after")
    def _validate_percentile_range(self) -> RenderConfigSchema:
        if self.pmin >= self.pmax:
            raise ValueError("pmin debe ser menor que pmax")
        return self


class HistogramResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bin_centers: list[float]
    counts: list[int]
    minimum: float
    maximum: float
