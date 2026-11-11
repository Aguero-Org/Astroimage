from __future__ import annotations

import numpy as np
import pandas as pd


def _ranked(frame: pd.DataFrame, columns: list[str], max_sources: int) -> pd.DataFrame:
    ordered = frame.sort_values(columns, ascending=False)
    limited = ordered.head(max_sources) if max_sources > 0 else ordered
    result = limited.reset_index(drop=True).copy()
    result["rank"] = np.arange(1, len(result) + 1)
    result["relevant"] = True
    return result


def select_point_sources(
    sources: pd.DataFrame | None,
    *,
    min_snr: float = 6.0,
    min_score: float = 0.18,
    max_sources: int = 50,
) -> pd.DataFrame | None:
    if sources is None or len(sources) == 0:
        return sources

    by_snr = sources[np.isfinite(sources["snr"]) & (sources["snr"] >= min_snr)].copy()
    if len(by_snr) == 0:
        return by_snr
    scored = (
        by_snr[by_snr["relevance_score"] >= min_score].copy()
        if "relevance_score" in by_snr.columns
        else by_snr
    )
    if len(scored) == 0:
        return scored
    return _ranked(scored, ["relevance_score", "snr"], max_sources)


def select_extended_sources(
    sources: pd.DataFrame | None,
    *,
    min_score: float = 0.20,
    max_sources: int = 3,
) -> pd.DataFrame | None:
    if sources is None or len(sources) == 0:
        return sources

    scored = sources.copy()
    if "relevance_score" in scored.columns:
        scored = scored[
            np.isfinite(scored["relevance_score"]) & (scored["relevance_score"] >= min_score)
        ].copy()
    if len(scored) == 0:
        return scored
    result = _ranked(scored, ["relevance_score", "area_pixels", "peak"], max_sources)
    result["source_id"] = np.arange(1, len(result) + 1)
    return result
