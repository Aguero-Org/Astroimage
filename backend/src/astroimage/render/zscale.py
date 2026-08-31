from __future__ import annotations

import math

import numpy as np

MAX_REJECT = 0.5
MIN_NPIXELS = 5
KREJ = 2.5
MAX_ITERATIONS = 5
MAX_SAMPLES = 1200
DEFAULT_CONTRAST = 0.25


def _sample_pixels(data: np.ndarray, max_pixels: int) -> np.ndarray:
    height, width = data.shape
    columns, rows = max(1, width), max(1, height)
    stride = max(1.0, math.sqrt((columns - 1) * (rows - 1) / max_pixels))
    stride_step = int(stride)

    samples: list[float] = []
    for x in range(0, columns, stride_step):
        for y in range(0, rows, stride_step):
            if len(samples) >= max_pixels:
                break
            value = float(data[y, x])
            if math.isfinite(value):
                samples.append(value)
    return np.asarray(samples, dtype=float)


def _compute_sigma(residuals: np.ndarray, good_pixels: np.ndarray) -> float:
    good = residuals[good_pixels]
    count = good.size
    if count <= 1:
        return 0.0
    return float(np.std(good, ddof=1)) if count > 1 else 0.0


def _window_sum(bad_pixels: np.ndarray, window: int) -> np.ndarray:
    count = bad_pixels.size
    half = window // 2
    output = np.zeros(count, dtype=int)
    for index in range(count):
        low = max(0, index - half)
        high = min(count, index + half)
        output[index] = int(np.sum(bad_pixels[low:high]))
    return output


def _fit_line(
    samples: np.ndarray,
    rejection: float,
    growth_window: int,
    max_iterations: int,
) -> tuple[int, float, float]:
    count = samples.size
    min_pixels = max(MIN_NPIXELS, int(count * MAX_REJECT))
    scale = 2.0 / (count - 1)
    normalized_x = np.arange(count, dtype=float) * scale - 1.0
    good_pixels = np.ones(count, dtype=bool)
    last_good = count + 1

    for _ in range(max_iterations):
        good_count = int(np.sum(good_pixels))
        if good_count >= last_good or good_count < min_pixels:
            break

        x_values = normalized_x[good_pixels]
        y_values = samples[good_pixels]
        sum_x = float(x_values.sum())
        sum_y = float(y_values.sum())
        sum_xx = float((x_values * x_values).sum())
        sum_xy = float((x_values * y_values).sum())
        delta = good_count * sum_xx - sum_x * sum_x
        intercept = (sum_xx * sum_y - sum_x * sum_xy) / delta
        slope = (good_count * sum_xy - sum_x * sum_y) / delta

        residuals = samples - (normalized_x * slope + intercept)
        sigma = _compute_sigma(residuals, good_pixels)
        threshold = sigma * rejection
        bad_pixels = (residuals < -threshold) | (residuals > threshold)
        grown = _window_sum(bad_pixels, growth_window)

        last_good = good_count
        good_pixels = grown == 0

    good_count = int(np.sum(good_pixels))
    return good_count, intercept - slope, slope * scale


def zscale_bounds(data: np.ndarray) -> tuple[float, float]:
    image = np.asarray(data, dtype=float)
    if image.ndim != 2:
        raise ValueError(f"The image must be 2D, received {image.ndim}D")

    samples = _sample_pixels(image, MAX_SAMPLES)
    if samples.size == 0:
        return 0.0, 1.0

    sorted_samples = np.sort(samples)
    sample_min = float(sorted_samples[0])
    sample_max = float(sorted_samples[-1])
    if sorted_samples.size < MIN_NPIXELS:
        return sample_min, sample_max
    if not sample_max > sample_min:
        return sample_min - 0.5, sample_max + 0.5

    center_pixel = (sorted_samples.size - 1) // 2
    if sorted_samples.size % 2 == 0:
        median = 0.5 * (
            float(sorted_samples[center_pixel]) + float(sorted_samples[center_pixel + 1])
        )
    else:
        median = float(sorted_samples[center_pixel])

    good_count, _, slope = _fit_line(
        sorted_samples,
        KREJ,
        max(1, int(sorted_samples.size * 0.01)),
        MAX_ITERATIONS,
    )

    if good_count < max(MIN_NPIXELS, sorted_samples.size * MAX_REJECT):
        return sample_min, sample_max

    fitted_slope = slope / DEFAULT_CONTRAST
    low = max(sample_min, median - (center_pixel - 1) * fitted_slope)
    high = min(sample_max, median + (sorted_samples.size - center_pixel) * fitted_slope)
    return float(low), float(high)
