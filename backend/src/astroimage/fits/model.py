from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class FitsTableInfo:
    index: int
    name: str
    rows: int
    columns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FitsMetadata:
    source_name: str | None
    hdu_index: int
    shape: tuple[int, ...] | None
    telescope: str | None
    instrument: str | None
    detector: str | None
    filter_name: str | None
    exptime: float | None
    date_obs: str | None
    time_obs: str | None
    photflam: float | None
    photplam: float | None
    photbw: float | None
    naxis: int | None
    naxis1: int | None
    naxis2: int | None
    crval1: float | None
    crval2: float | None
    crpix1: float | None
    crpix2: float | None
    ctype1: str | None
    ctype2: str | None
    cd1_1: float | None
    cd1_2: float | None
    cd2_1: float | None
    cd2_2: float | None
    cdelt1: float | None
    cdelt2: float | None
    image_hdus: tuple[int, ...]
    tables: tuple[FitsTableInfo, ...]
    header: dict[str, Any] = field(default_factory=dict)
