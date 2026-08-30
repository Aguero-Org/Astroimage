from __future__ import annotations

import numpy as np
import pandas as pd
from astropy.table import Table
from photutils.detection import DAOStarFinder
from scipy.spatial import cKDTree

_EMPTY_COLUMNS = [
    "source_id",
    "xcentroid",
    "ycentroid",
    "snr",
    "relevance_score",
    "point_source",
]


def _find_column(table: Table, candidates: list[str]) -> str | None:
    normalized = {
        str(column).strip().lower().replace("_", ""): str(column) for column in table.colnames
    }
    for candidate in candidates:
        key = candidate.lower().replace("_", "")
        if key in normalized:
            return normalized[key]
    return None


def _scalar_rms(background_rms: np.ndarray) -> float:
    rms = float(np.nanmedian(background_rms))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError(f"Background RMS inválido: {rms}")
    return rms


def _run_starfinder(data_sub: np.ndarray, rms: float, fwhm: float, sigma: float) -> Table | None:
    finder = DAOStarFinder(fwhm=fwhm, threshold=sigma * rms, exclude_border=True)
    return finder(data_sub)


def _table_to_frame(table: Table) -> pd.DataFrame:
    coordinate_x = _find_column(table, ["xcentroid", "x_centroid", "x"])
    coordinate_y = _find_column(table, ["ycentroid", "y_centroid", "y"])
    if coordinate_x is None or coordinate_y is None:
        raise RuntimeError(f"No se encontraron coordenadas X/Y. Columnas: {list(table.colnames)}")

    data: dict[str, np.ndarray] = {
        "source_id": np.arange(1, len(table) + 1),
        "xcentroid": np.asarray(table[coordinate_x], dtype=float),
        "ycentroid": np.asarray(table[coordinate_y], dtype=float),
    }

    for column in table.colnames:
        if column in (coordinate_x, coordinate_y):
            continue
        values = np.asarray(table[column])
        if values.ndim == 1 and len(values) == len(table):
            data[str(column)] = values

    return pd.DataFrame(data)


def _add_snr(sources: pd.DataFrame, rms: float) -> pd.DataFrame:
    if "peak" in sources.columns:
        sources["snr"] = sources["peak"].astype(float) / rms
    elif "flux" in sources.columns:
        sources["snr"] = sources["flux"].astype(float) / rms
    else:
        sources["snr"] = np.nan
    return sources


def _apply_morphology_filters(sources: pd.DataFrame, sigma: float) -> pd.DataFrame:
    thresholded = sources[np.isfinite(sources["snr"]) & (sources["snr"] >= sigma)].copy()

    if len(thresholded) == 0:
        return thresholded

    if "sharpness" in thresholded.columns:
        sharpness = thresholded["sharpness"].astype(float)
        thresholded = thresholded[
            np.isfinite(sharpness) & (sharpness >= 0.20) & (sharpness <= 1.00)
        ].copy()

    if len(thresholded) == 0:
        return thresholded

    if "roundness1" in thresholded.columns:
        roundness = np.abs(thresholded["roundness1"].astype(float))
        thresholded = thresholded[np.isfinite(roundness) & (roundness <= 0.50)].copy()

    return thresholded


def _photometric_scores(sources: pd.DataFrame, sigma: float) -> pd.DataFrame:
    snr = sources["snr"].astype(float)
    sources["snr_score"] = np.clip(
        (np.log10(np.maximum(snr, 1.0)) - np.log10(sigma)) / np.log10(100.0 / sigma),
        0,
        1,
    )

    if "peak" in sources.columns:
        peak = sources["peak"].astype(float)
        positive_peak = peak[np.isfinite(peak) & (peak > 0)]
        if len(positive_peak) > 0:
            log_peak = np.log1p(np.maximum(peak, 0))
            high_ref = np.percentile(log_peak[np.isfinite(log_peak)], 90)
            low_ref = np.percentile(log_peak[np.isfinite(log_peak)], 10)
            sources["peak_score"] = np.clip(
                (log_peak - low_ref) / max(high_ref - low_ref, 1e-12),
                0,
                1,
            )
        else:
            sources["peak_score"] = 0.0
    else:
        sources["peak_score"] = sources["snr_score"]

    if "flux" in sources.columns:
        flux = sources["flux"].astype(float)
        positive_flux = flux[np.isfinite(flux) & (flux > 0)]
        if len(positive_flux) > 0:
            log_flux = np.log1p(np.maximum(flux, 0))
            high_ref = np.percentile(log_flux[np.isfinite(log_flux)], 90)
            low_ref = np.percentile(log_flux[np.isfinite(log_flux)], 10)
            sources["flux_score"] = np.clip(
                (log_flux - low_ref) / max(high_ref - low_ref, 1e-12),
                0,
                1,
            )
        else:
            sources["flux_score"] = 0.0
    else:
        sources["flux_score"] = 0.0

    sources["brightness_score"] = (
        0.55 * sources["peak_score"] + 0.45 * sources["flux_score"]
    ).clip(0.0, 1.0)

    return sources


def _visual_metrics(
    sources: pd.DataFrame,
    *,
    data_sub: np.ndarray,
    rms: float,
    visual_area_radius: float,
    visual_area_sigma: float,
) -> pd.DataFrame:
    visual_radius = max(float(visual_area_radius), 1.5)
    visual_sigma = max(float(visual_area_sigma), 0.5)
    visual_threshold = visual_sigma * rms
    image = np.asarray(data_sub, dtype=float)
    height, width = image.shape
    apparent_area: list[float] = []
    apparent_flux: list[float] = []
    apparent_peak: list[float] = []

    for coordinate_x, coordinate_y in zip(
        sources["xcentroid"].to_numpy(dtype=float),
        sources["ycentroid"].to_numpy(dtype=float),
        strict=True,
    ):
        center_x, center_y = round(coordinate_x), round(coordinate_y)
        radius = int(np.ceil(visual_radius))
        x0, x1 = max(0, center_x - radius), min(width, center_x + radius + 1)
        y0, y1 = max(0, center_y - radius), min(height, center_y + radius + 1)
        patch = image[y0:y1, x0:x1]
        if patch.size == 0:
            apparent_area.append(0.0)
            apparent_flux.append(0.0)
            apparent_peak.append(0.0)
            continue
        adj_y, adj_x = np.mgrid[y0:y1, x0:x1]
        inside = ((adj_x - coordinate_x) ** 2 + (adj_y - coordinate_y) ** 2) <= visual_radius**2
        signal = np.isfinite(patch) & inside & (patch > visual_threshold)
        values = patch[signal]
        apparent_area.append(float(values.size))
        if values.size:
            apparent_flux.append(float(np.sum(np.maximum(values, 0.0))))
            apparent_peak.append(float(np.max(values)))
        else:
            apparent_flux.append(0.0)
            apparent_peak.append(0.0)

    sources["apparent_area"] = np.asarray(apparent_area, dtype=float)
    sources["apparent_flux"] = np.asarray(apparent_flux, dtype=float)
    sources["apparent_peak"] = np.asarray(apparent_peak, dtype=float)

    return sources


def _visual_scores(sources: pd.DataFrame, *, rms: float) -> pd.DataFrame:
    area_log = np.log1p(np.maximum(sources["apparent_area"].to_numpy(dtype=float), 0.0))
    finite_area = area_log[np.isfinite(area_log)]
    if finite_area.size:
        low_ref = np.percentile(finite_area, 10)
        high_ref = np.percentile(finite_area, 90)
        sources["visual_area_score"] = np.clip(
            (area_log - low_ref) / max(high_ref - low_ref, 1e-12), 0, 1
        )
    else:
        sources["visual_area_score"] = 0.0

    contrast = np.maximum(sources["apparent_peak"].to_numpy(dtype=float), 0.0) / max(rms, 1e-30)
    finite_contrast = contrast[np.isfinite(contrast)]
    contrast_ref = (
        max(float(np.percentile(finite_contrast, 90)), 1.0) if finite_contrast.size else 1.0
    )
    sources["visual_contrast_score"] = np.clip(np.log1p(contrast) / np.log1p(contrast_ref), 0, 1)

    if "npix" in sources.columns:
        npix_values = (
            pd.to_numeric(sources["npix"], errors="coerce").fillna(0).to_numpy(dtype=float)
        )
        npix_low = max(float(np.percentile(npix_values, 10)), 0)
        npix_high = max(float(np.percentile(npix_values, 90)), 0)
        sources["visual_size_score"] = np.clip(
            (np.log1p(np.maximum(npix_values, 0)) - np.log1p(npix_low))
            / max(np.log1p(npix_high) - np.log1p(npix_low), 1e-12),
            0,
            1,
        )
    else:
        sources["visual_size_score"] = sources["visual_area_score"]

    sources["visual_score"] = (
        0.35 * sources["peak_score"]
        + 0.15 * sources["flux_score"]
        + 0.30 * sources["visual_area_score"]
        + 0.20 * sources["visual_contrast_score"]
    )

    return sources


def _morphology_scores(sources: pd.DataFrame) -> pd.DataFrame:
    if "sharpness" in sources.columns:
        sharpness = sources["sharpness"].astype(float)
        sources["sharpness_score"] = np.exp(-(((sharpness - 0.5) / 0.28) ** 2))
    else:
        sources["sharpness_score"] = 1.0

    if "roundness1" in sources.columns:
        roundness = np.abs(sources["roundness1"].astype(float))
        sources["roundness_score"] = np.exp(-((roundness / 0.28) ** 2))
    else:
        sources["roundness_score"] = 1.0

    sources["morphology_score"] = (
        0.45 * sources["snr_score"]
        + 0.35 * sources["sharpness_score"]
        + 0.20 * sources["roundness_score"]
    )

    return sources


def _relevance_and_sort(sources: pd.DataFrame, visual_weight: float) -> pd.DataFrame:
    clipped_visual_weight = float(np.clip(visual_weight, 0.0, 1.0))
    sources["relevance_score"] = np.clip(
        clipped_visual_weight * sources["visual_score"]
        + (1.0 - clipped_visual_weight) * sources["morphology_score"],
        0,
        1,
    )

    sources.sort_values(
        ["relevance_score", "snr"],
        ascending=False,
        inplace=True,
    )

    return sources


def _non_maximum_suppression(sources: pd.DataFrame, min_distance: float) -> pd.DataFrame:
    positions = sources[["xcentroid", "ycentroid"]].to_numpy(dtype=float)
    keep = np.ones(len(sources), dtype=bool)

    if len(positions) > 1:
        tree = cKDTree(positions)

        for index in range(len(positions)):
            if not keep[index]:
                continue
            nearby = tree.query_ball_point(positions[index], r=float(min_distance))
            for neighbor_index in nearby:
                if neighbor_index > index:
                    keep[neighbor_index] = False

    return sources.iloc[keep].copy()


def _apply_isolation_and_rank(sources: pd.DataFrame, min_distance: float) -> pd.DataFrame:
    if len(sources) > 1:
        positions = sources[["xcentroid", "ycentroid"]].to_numpy(dtype=float)
        tree = cKDTree(positions)
        nearest = tree.query(positions, k=2)[0][:, 1]
        isolation_ref = max(float(min_distance) * 8.0, 1.0)
        sources["isolation_score"] = np.clip(nearest / isolation_ref, 0, 1)
    else:
        sources["isolation_score"] = 1.0

    sources["relevance_score"] = np.clip(
        0.92 * sources["relevance_score"] + 0.08 * sources["isolation_score"],
        0,
        1,
    )

    sources.sort_values(
        ["relevance_score", "visual_score", "snr"],
        ascending=[False, False, False],
        inplace=True,
    )

    sources.reset_index(drop=True, inplace=True)
    sources["rank"] = np.arange(1, len(sources) + 1)
    sources["point_source"] = True
    sources["relevant"] = True

    return sources


def detect_point_sources(
    data_sub: np.ndarray,
    background_rms: np.ndarray,
    fwhm: float = 5.5,
    sigma: float = 9.0,
    min_distance: float = 4.0,
    visual_area_radius: float = 7.0,
    visual_area_sigma: float = 2.0,
    visual_weight: float = 0.80,
) -> pd.DataFrame:
    rms = _scalar_rms(background_rms)
    table = _run_starfinder(data_sub, rms, fwhm, sigma)

    if table is None or len(table) == 0:
        return pd.DataFrame(columns=_EMPTY_COLUMNS)

    candidate_sources = _table_to_frame(table)
    sources_with_snr = _add_snr(candidate_sources, rms)
    surviving_sources = _apply_morphology_filters(sources_with_snr, sigma)

    if len(surviving_sources) == 0:
        return surviving_sources

    sources_with_photometry = _photometric_scores(surviving_sources, sigma)
    sources_with_appearance = _visual_metrics(
        sources_with_photometry,
        data_sub=data_sub,
        rms=rms,
        visual_area_radius=visual_area_radius,
        visual_area_sigma=visual_area_sigma,
    )
    sources_with_visual_scores = _visual_scores(sources_with_appearance, rms=rms)
    sources_with_morphology = _morphology_scores(sources_with_visual_scores)
    sources_with_relevance = _relevance_and_sort(sources_with_morphology, visual_weight)
    sources_after_nms = _non_maximum_suppression(sources_with_relevance, min_distance)
    final_sources = _apply_isolation_and_rank(sources_after_nms, min_distance)

    return final_sources
