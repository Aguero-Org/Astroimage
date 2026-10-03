from __future__ import annotations

import numpy as np
import pandas as pd


def select_point_sources(
    sources: pd.DataFrame | None,
    *,
    min_snr: float = 6.0,
    min_score: float = 0.18,
    max_sources: int = 50,
) -> pd.DataFrame | None:
    if sources is None or len(sources) == 0:
        return sources

    result = sources[np.isfinite(sources["snr"]) & (sources["snr"] >= min_snr)].copy()

    if len(result) == 0:
        return result

    if "relevance_score" in result.columns:
        result = result[result["relevance_score"] >= min_score].copy()

    if len(result) == 0:
        return result

    result.sort_values(["relevance_score", "snr"], ascending=False, inplace=True)

    if max_sources > 0:
        result = result.head(max_sources).copy()

    result.reset_index(drop=True, inplace=True)
    result["rank"] = np.arange(1, len(result) + 1)
    result["relevant"] = True

    return result


def select_extended_sources(
    sources: pd.DataFrame | None,
    *,
    min_score: float = 0.20,
    max_sources: int = 3,
) -> pd.DataFrame | None:
    if sources is None or len(sources) == 0:
        return sources

    result = sources.copy()

    if "relevance_score" in result.columns:
        result = result[
            np.isfinite(result["relevance_score"]) & (result["relevance_score"] >= min_score)
        ].copy()

    if len(result) == 0:
        return result

    result.sort_values(
        ["relevance_score", "area_pixels", "peak"],
        ascending=False,
        inplace=True,
    )

    if max_sources > 0:
        result = result.head(max_sources).copy()

    result.reset_index(drop=True, inplace=True)
    result["source_id"] = np.arange(1, len(result) + 1)
    result["rank"] = np.arange(1, len(result) + 1)
    result["relevant"] = True

    return result
