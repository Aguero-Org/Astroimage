from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import ndimage

_EMPTY_COLUMNS = [
    "source_id",
    "xcentroid",
    "ycentroid",
    "width_pixels",
    "height_pixels",
    "area_pixels",
    "peak",
    "mean",
    "flux",
    "relevance_score",
]

_STRUCTURE = np.ones((3, 3), dtype=bool)
_CLOSING_STRUCTURE = np.ones((5, 5), dtype=bool)


def _bin_image(image: np.ndarray, factor: int) -> np.ndarray:
    if factor <= 1:
        return image
    height, width = image.shape
    binned_height = height // factor
    binned_width = width // factor
    if binned_height < 1 or binned_width < 1:
        return image
    trimmed = image[: binned_height * factor, : binned_width * factor]
    with np.errstate(invalid="ignore"):
        binned = trimmed.reshape(
            binned_height,
            factor,
            binned_width,
            factor,
        ).mean(axis=(1, 3))
    return binned


def _build_mask(
    clean: np.ndarray,
    finite: np.ndarray,
    threshold: float,
    *,
    opening_iterations: int,
    closing_iterations: int,
) -> np.ndarray:
    mask = finite & (clean > threshold)
    if opening_iterations > 0:
        mask = ndimage.binary_opening(
            mask,
            structure=_STRUCTURE,
            iterations=opening_iterations,
        )
    if closing_iterations > 0:
        mask = ndimage.binary_closing(
            mask,
            structure=_CLOSING_STRUCTURE,
            iterations=closing_iterations,
        )
    mask = ndimage.binary_dilation(mask, structure=_STRUCTURE, iterations=1)
    return np.asarray(ndimage.binary_fill_holes(mask), dtype=bool)


def _work_rms(
    smooth: np.ndarray,
    finite: np.ndarray,
    background_rms: np.ndarray | None,
    factor: int,
) -> float:
    if background_rms is not None:
        try:
            external_rms = float(np.nanmedian(np.asarray(background_rms)))
        except Exception:
            external_rms = np.nan
    else:
        external_rms = np.nan

    local_mad = float(np.nanmedian(np.abs(smooth[finite] - np.nanmedian(smooth[finite]))))
    robust_rms = 1.4826 * local_mad

    if not np.isfinite(robust_rms) or robust_rms <= 0:
        robust_rms = float(np.nanstd(smooth[finite]))

    if np.isfinite(external_rms) and external_rms > 0:
        bin_noise = external_rms / max(factor, 1)
        work_rms = max(robust_rms, bin_noise)
    else:
        work_rms = robust_rms

    if not np.isfinite(work_rms) or work_rms <= 0:
        work_rms = 1e-12

    return work_rms


def _apparent_regions(
    smooth: np.ndarray,
    labeled: np.ndarray,
    factor: int,
    *,
    median: float,
    min_area: int,
    max_area: int | None,
    edge_margin: float,
) -> list[dict[str, object]]:
    binned_height, binned_width = labeled.shape
    min_area_binned = max(10, int(np.ceil(float(min_area) / (factor**2))))
    max_area_binned = int(max_area / (factor**2)) if max_area is not None else None
    edge_x = max(2, int(binned_width * edge_margin))
    edge_y = max(2, int(binned_height * edge_margin))

    rows: list[dict[str, object]] = []

    for label_id, object_slice in enumerate(
        ndimage.find_objects(labeled),
        start=1,
    ):
        if object_slice is None:
            continue

        component = labeled[object_slice] == label_id
        component_area = int(np.count_nonzero(component))

        if component_area < min_area_binned:
            continue
        if max_area_binned is not None and component_area > max_area_binned:
            continue

        y_slice, x_slice = object_slice
        x_start = int(x_slice.start)
        x_stop = int(x_slice.stop)
        y_start = int(y_slice.start)
        y_stop = int(y_slice.stop)

        width = (x_stop - x_start) * factor
        height = (y_stop - y_start) * factor
        area_pixels = component_area * factor * factor
        touches_edge = (
            x_start <= edge_x
            or y_start <= edge_y
            or x_stop >= binned_width - edge_x
            or y_stop >= binned_height - edge_y
        )

        values = smooth[object_slice][component]
        if values.size == 0:
            continue

        peak = float(np.max(values))
        mean = float(np.mean(values))
        flux = float(np.sum(np.maximum(values - median, 0)))

        center_y, center_x = ndimage.center_of_mass(smooth, labeled, label_id)
        xcenter = float(center_x * factor)
        ycenter = float(center_y * factor)

        aspect_ratio = max(width, height) / max(min(width, height), 1.0)
        if aspect_ratio > 12.0 and area_pixels < max(min_area * 10, 5000):
            continue

        rows.append(
            {
                "source_id": len(rows) + 1,
                "xcentroid": xcenter,
                "ycentroid": ycenter,
                "width_pixels": float(width),
                "height_pixels": float(height),
                "area_pixels": int(area_pixels),
                "peak": peak,
                "mean": mean,
                "flux": flux,
                "touches_edge": bool(touches_edge),
                "aspect_ratio": float(aspect_ratio),
            }
        )

    return rows


def _score_regions(
    regions: pd.DataFrame,
    *,
    median: float,
    work_rms: float,
    threshold: float,
) -> pd.DataFrame:
    area_ref = max(float(regions["area_pixels"].quantile(0.90)), 1.0)
    peak_ref = max(float(regions["peak"].quantile(0.90)), threshold)

    regions["area_score"] = np.clip(
        np.log1p(regions["area_pixels"]) / np.log1p(area_ref),
        0,
        1,
    )
    regions["brightness_score"] = np.clip(
        (regions["peak"] - median) / max(peak_ref - median, work_rms, 1e-30),
        0,
        1,
    )
    regions["compactness_score"] = np.clip(
        1.0 / np.maximum(regions["aspect_ratio"], 1.0),
        0,
        1,
    )
    regions["edge_score"] = np.where(regions["touches_edge"], 0.25, 1.0)
    regions["relevance_score"] = (
        0.50 * regions["area_score"]
        + 0.30 * regions["brightness_score"]
        + 0.10 * regions["compactness_score"]
        + 0.10 * regions["edge_score"]
    )
    return regions


def _merge_overlapping(regions: pd.DataFrame, *, factor: int) -> pd.DataFrame:
    regions = regions.sort_values("relevance_score", ascending=False)

    kept: list[int] = []

    for index, row in regions.iterrows():
        coordinate_x = float(row["xcentroid"])
        coordinate_y = float(row["ycentroid"])
        width = float(row["width_pixels"])
        height = float(row["height_pixels"])

        duplicate = False

        for kept_index in kept:
            other = regions.loc[kept_index]
            other_x = float(other["xcentroid"])
            other_y = float(other["ycentroid"])
            other_width = float(other["width_pixels"])
            other_height = float(other["height_pixels"])

            distance = np.hypot(coordinate_x - other_x, coordinate_y - other_y)
            merge_radius = 0.25 * min(
                max(width, height),
                max(other_width, other_height),
            )

            if distance <= max(merge_radius, factor * 4):
                duplicate = True
                break

        if not duplicate:
            kept.append(index)

    regions = (
        regions.loc[kept]
        .sort_values(
            "relevance_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )
    regions["source_id"] = np.arange(1, len(regions) + 1)
    regions["relevant"] = True
    return regions


def detect_extended_sources(
    data: np.ndarray,
    *,
    background_rms: np.ndarray | None = None,
    sigma: float = 3.0,
    smooth_sigma: float = 8.0,
    min_area: int = 500,
    bin_factor: int = 8,
    max_area: int | None = None,
    closing_iterations: int = 2,
    opening_iterations: int = 1,
    edge_margin: float = 0.03,
) -> pd.DataFrame:
    image = np.asarray(data, dtype=float)
    image = np.nan_to_num(image, nan=0.0, posinf=0.0, neginf=0.0)

    if image.ndim != 2:
        raise ValueError(f"Image must be 2D. Received shape: {image.shape}")

    height, width = image.shape
    factor = max(int(bin_factor), 1)

    binned_height = height // factor
    binned_width = width // factor

    if binned_height < 10 or binned_width < 10:
        factor = 1
        binned_height, binned_width = height, width

    binned = _bin_image(image, factor)
    finite = np.isfinite(binned)

    if not np.any(finite):
        return pd.DataFrame(columns=_EMPTY_COLUMNS)

    median = float(np.nanmedian(binned[finite]))
    clean = np.where(finite, binned, median)

    smooth_sigma_work = max(float(smooth_sigma) / factor, 0.5)
    smooth = ndimage.gaussian_filter(clean, sigma=smooth_sigma_work)

    work_rms = _work_rms(smooth, finite, background_rms, factor)
    threshold = median + float(sigma) * work_rms
    mask = _build_mask(
        smooth,
        finite,
        threshold,
        opening_iterations=opening_iterations,
        closing_iterations=closing_iterations,
    )

    labeled, label_count = ndimage.label(mask, structure=_STRUCTURE)

    if label_count == 0:
        return pd.DataFrame(columns=_EMPTY_COLUMNS)

    rows = _apparent_regions(
        smooth,
        labeled,
        factor,
        median=median,
        min_area=min_area,
        max_area=max_area,
        edge_margin=edge_margin,
    )
    regions = pd.DataFrame(rows)

    if regions.empty:
        return regions

    scored = _score_regions(
        regions,
        median=median,
        work_rms=work_rms,
        threshold=threshold,
    )
    return _merge_overlapping(scored, factor=factor)
