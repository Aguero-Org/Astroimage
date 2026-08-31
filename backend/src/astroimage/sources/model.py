from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict


@dataclass(frozen=True)
class BackgroundModel:
    background: np.ndarray
    background_rms: np.ndarray
    data_sub: np.ndarray


class PointSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: int
    rank: int
    xcentroid: float
    ycentroid: float
    snr: float
    relevance_score: float
    peak: float | None = None
    flux: float | None = None
    object_type: Literal["point"] = "point"


class ExtendedSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: int
    rank: int
    object_type: Literal["extended"] = "extended"


@dataclass(frozen=True)
class SourceDetectionResult:
    source_name: str | None
    point_sources: list[PointSource] = field(default_factory=list)
    extended_sources: list[ExtendedSource] = field(default_factory=list)
