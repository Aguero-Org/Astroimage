from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import ndimage

_EXTENDED_COLUMNS = [
    "source_id",
    "rank",
    "xcentroid",
    "ycentroid",
    "snr",
    "peak",
    "flux",
    "object_type",
]

_EDGE_MARGIN = 0.03
_EDGE_PENALTY = 0.25
_BIN_FACTOR = 8
_MIN_AREA = 8000
_SMOOTH_SIGMA = 8.0
_CLOSING_ITERATIONS = 2
_OPENING_ITERATIONS = 1


def _bin_mean(image: np.ndarray, factor: int) -> np.ndarray:
    if factor <= 1:
        return image

    height, width = image.shape
    new_height = height // factor
    new_width = width // factor
    if new_height < 1 or new_width < 1:
        return image

    trimmed = image[: new_height * factor, : new_width * factor]
    reshaped = trimmed.reshape(new_height, factor, new_width, factor)
    with np.errstate(invalid="ignore"):
        return np.nanmean(reshaped, axis=(1, 3))


def _robust_sigma(background_rms: np.ndarray) -> float:
    values = np.asarray(background_rms, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan")
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    if mad > 0:
        return 1.4826 * mad
    return float(np.std(values))


def _scalar_rms(background_rms: np.ndarray) -> float:
    rms = float(np.nanmedian(background_rms))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError(f"Invalid background RMS: {rms}")
    return rms


def _optional(value: float) -> float | None:
    if np.isfinite(value):
        return float(value)
    return None


def detect_extended_sources(
    data: np.ndarray,
    background_rms: np.ndarray,
    *,
    sigma: float,
    min_snr: float,
    max_sources: int,
) -> pd.DataFrame:
    image = np.asarray(data, dtype=float)
    image = np.nan_to_num(image, nan=0.0, posinf=0.0, neginf=0.0)
    background_noise = _scalar_rms(background_rms)

    factor = max(int(_BIN_FACTOR), 1)
    height, width = image.shape
    bin_height = height // factor
    bin_width = width // factor
    if bin_height < 10 or bin_width < 10:
        factor = 1
        bin_height, bin_width = height, width

    cropped = image[: bin_height * factor, : bin_width * factor]
    with np.errstate(invalid="ignore"):
        binned = cropped.reshape(
            bin_height,
            factor,
            bin_width,
            factor,
        ).mean(axis=(1, 3))

    finite = np.isfinite(binned)
    if not np.any(finite):
        return pd.DataFrame(columns=_EXTENDED_COLUMNS)

    median = float(np.nanmedian(binned[finite]))
    clean = np.where(finite, binned, median)
    smooth_sigma_work = max(float(_SMOOTH_SIGMA) / factor, 0.5)
    smooth = ndimage.gaussian_filter(clean, sigma=smooth_sigma_work)

    external_rms = background_noise
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

    threshold = median + float(sigma) * work_rms
    binary_mask = finite & (smooth > threshold)

    structure = np.ones((3, 3), dtype=bool)
    if _OPENING_ITERATIONS > 0:
        binary_mask = ndimage.binary_opening(
            binary_mask,
            structure=structure,
            iterations=int(_OPENING_ITERATIONS),
        )
    if _CLOSING_ITERATIONS > 0:
        binary_mask = ndimage.binary_closing(
            binary_mask,
            structure=np.ones((5, 5), dtype=bool),
            iterations=int(_CLOSING_ITERATIONS),
        )
    binary_mask = ndimage.binary_dilation(
        binary_mask,
        structure=structure,
        iterations=1,
    )
    binary_mask = ndimage.binary_fill_holes(binary_mask)

    labels, label_count = ndimage.label(binary_mask, structure=structure)
    if label_count == 0:
        return pd.DataFrame(columns=_EXTENDED_COLUMNS)

    objects = ndimage.find_objects(labels)
    min_area_binned = max(10, int(np.ceil(float(_MIN_AREA) / (factor**2))))
    max_area_binned: int | None = None

    edge_x = max(2, int(bin_width * _EDGE_MARGIN))
    edge_y = max(2, int(bin_height * _EDGE_MARGIN))

    rows: list[dict[str, object]] = []
    for label_id, label_object in enumerate(objects, start=1):
        if label_object is None:
            continue

        coordinate_slice_y, coordinate_slice_x = label_object
        component = labels[label_object] == label_id
        area = int(np.count_nonzero(component))
        if area < min_area_binned:
            continue
        if max_area_binned is not None and area > max_area_binned:
            continue

        x_start, x_stop = coordinate_slice_x.start, coordinate_slice_x.stop
        y_start, y_stop = coordinate_slice_y.start, coordinate_slice_y.stop
        width = (x_stop - x_start) * factor
        height = (y_stop - y_start) * factor
        area_pixels = area * factor * factor

        touches_edge = bool(
            x_start <= edge_x
            or y_start <= edge_y
            or x_stop >= bin_width - edge_x
            or y_stop >= bin_height - edge_y
        )

        values = smooth[label_object][component]
        if values.size == 0:
            continue

        peak = float(np.max(values))
        mean = float(np.mean(values))
        flux = float(np.sum(np.maximum(values - median, 0)))

        mass_y, mass_x = ndimage.center_of_mass(smooth, labels, label_id)
        centroid_x = float(mass_x * factor)
        centroid_y = float(mass_y * factor)

        aspect = max(width, height) / max(min(width, height), 1.0)
        if aspect > 12.0 and area_pixels < max(_MIN_AREA * 10, 5000):
            continue

        rows.append(
            {
                "xcentroid": centroid_x,
                "ycentroid": centroid_y,
                "width_pixels": float(width),
                "height_pixels": float(height),
                "area_pixels": int(area_pixels),
                "peak": peak,
                "mean": mean,
                "flux": flux,
                "touches_edge": touches_edge,
                "aspect_ratio": float(aspect),
            }
        )

    if not rows:
        return pd.DataFrame(columns=_EXTENDED_COLUMNS)

    result = pd.DataFrame(rows)
    area_reference = max(float(result["area_pixels"].quantile(0.90)), 1.0)
    peak_reference = max(float(result["peak"].quantile(0.90)), threshold)

    result["area_score"] = np.clip(
        np.log1p(result["area_pixels"]) / np.log1p(area_reference),
        0,
        1,
    )
    result["brightness_score"] = np.clip(
        (result["peak"] - median) / max(peak_reference - median, work_rms, 1e-30),
        0,
        1,
    )
    result["compactness_score"] = np.clip(
        1.0 / np.maximum(result["aspect_ratio"], 1.0),
        0,
        1,
    )
    result["edge_score"] = np.where(result["touches_edge"], _EDGE_PENALTY, 1.0)
    result["relevance_score"] = (
        0.50 * result["area_score"]
        + 0.30 * result["brightness_score"]
        + 0.10 * result["compactness_score"]
        + 0.10 * result["edge_score"]
    )

    result.sort_values("relevance_score", ascending=False, inplace=True)
    kept_indices: list[int] = []
    for index, row in result.iterrows():
        coordinate_x = float(row["xcentroid"])
        coordinate_y = float(row["ycentroid"])
        source_width = float(row["width_pixels"])
        source_height = float(row["height_pixels"])
        duplicate = False
        for kept_index in kept_indices:
            other = result.loc[kept_index]
            other_x = float(other["xcentroid"])
            other_y = float(other["ycentroid"])
            other_width = float(other["width_pixels"])
            other_height = float(other["height_pixels"])
            distance = np.hypot(coordinate_x - other_x, coordinate_y - other_y)
            merge_radius = 0.25 * min(
                max(source_width, source_height),
                max(other_width, other_height),
            )
            if distance <= max(merge_radius, factor * 4):
                duplicate = True
                break
        if not duplicate:
            kept_indices.append(int(index))

    result = result.loc[kept_indices].copy()
    result.sort_values("relevance_score", ascending=False, inplace=True)
    result.reset_index(drop=True, inplace=True)

    result["snr"] = result["peak"] / background_noise
    result = result[result["snr"] >= min_snr].copy()
    result.sort_values("relevance_score", ascending=False, inplace=True)
    result.reset_index(drop=True, inplace=True)

    if max_sources > 0 and len(result) > max_sources:
        result = result.head(max_sources).copy()

    output = pd.DataFrame(
        {
            "source_id": np.arange(1, len(result) + 1),
            "rank": np.arange(1, len(result) + 1),
            "xcentroid": result["xcentroid"].to_numpy(dtype=float),
            "ycentroid": result["ycentroid"].to_numpy(dtype=float),
            "snr": result["snr"].to_numpy(dtype=float),
            "peak": [_optional(value) for value in result["peak"].to_numpy(dtype=float)],
            "flux": [_optional(value) for value in result["flux"].to_numpy(dtype=float)],
            "object_type": ["extended"] * len(result),
        }
    )
    return output
