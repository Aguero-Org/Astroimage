from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Stretch = Literal["linear", "sqrt", "log", "asinh"]
Limits = Literal["percentiles", "zscale"]
Colormap = Literal["grey", "inverse", "heat", "rainbow", "cube_helix"]


@dataclass(frozen=True)
class RenderConfig:
    stretch: Stretch
    limits: Limits
    colormap: Colormap
    pmin: float
    pmax: float
    gamma: float


@dataclass(frozen=True)
class Histogram:
    bin_centers: list[float]
    counts: list[int]
    minimum: float
    maximum: float
