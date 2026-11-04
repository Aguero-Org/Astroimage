from __future__ import annotations

import numpy as np

from astroimage.render.spec import Histogram


def build_histogram(data: np.ndarray, bins: int) -> Histogram:
    values = np.asarray(data)[np.isfinite(data)]
    if values.size == 0:
        return Histogram(bin_centers=[], counts=[], minimum=0.0, maximum=0.0)

    counts, edges = np.histogram(values, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2.0
    return Histogram(
        bin_centers=centers.tolist(),
        counts=counts.tolist(),
        minimum=float(np.min(values)),
        maximum=float(np.max(values)),
    )
