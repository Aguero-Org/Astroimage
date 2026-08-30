from __future__ import annotations

import numpy as np
from astropy.stats import SigmaClip
from photutils.background import Background2D, MedianBackground

from astroimage.sources.model import BackgroundModel


def estimate_background(
    data: np.ndarray,
    *,
    box_size: int = 50,
    filter_size: int = 3,
    sigma: float = 3.0,
) -> BackgroundModel:
    clean = np.asarray(data, dtype=float).copy()
    finite = np.isfinite(clean)

    if not np.any(finite):
        raise ValueError("No hay valores finitos en la imagen.")

    median = float(np.nanmedian(clean))
    clean[~finite] = median

    background = Background2D(
        clean,
        box_size=(box_size, box_size),
        filter_size=(filter_size, filter_size),
        sigma_clip=SigmaClip(sigma=sigma),
        bkg_estimator=MedianBackground(),
    )

    rms = float(np.nanmedian(background.background_rms))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError(f"Background RMS inválido: {rms}")

    return BackgroundModel(
        background=background.background,
        background_rms=background.background_rms,
        data_sub=clean - background.background,
        clean_data=clean,
    )
