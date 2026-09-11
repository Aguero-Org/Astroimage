from __future__ import annotations

import numpy as np
import pandas as pd

from astroimage.sources.detection.filtering import select_point_sources


def _candidate_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_id": np.arange(1, 6),
            "xcentroid": np.arange(5, dtype=float),
            "ycentroid": np.arange(5, dtype=float),
            "snr": [4.0, 6.5, 11.0, 15.5, 20.0],
            "relevance_score": [0.9, 0.1, 0.6, 0.0, 0.4],
        }
    )


def test_select_filters_and_truncates_top_n() -> None:
    frame = _candidate_frame()

    selected = select_point_sources(
        frame,
        min_snr=6.0,
        min_score=0.2,
        max_sources=2,
    )

    assert selected is not None
    assert len(selected) == 2
    assert selected["relevance_score"].tolist() == [0.6, 0.4]
    assert selected["rank"].tolist() == [1, 2]
    assert selected["relevant"].all()


def test_select_returns_empty_for_empty_input() -> None:
    assert select_point_sources(None) is None
    empty_frame = pd.DataFrame(columns=["snr", "relevance_score"])
    selected = select_point_sources(empty_frame, min_snr=6.0)
    assert selected is None or len(selected) == 0


def test_select_filters_everything_out() -> None:
    frame = _candidate_frame()

    selected = select_point_sources(frame, min_snr=99.0)

    assert selected is not None
    assert len(selected) == 0
