from __future__ import annotations

SPEED_WINDOW_SECONDS = 5.0


def moving_average_bytes_per_second(
    samples: list[tuple[float, int]],
    *,
    now: float,
    window_seconds: float = SPEED_WINDOW_SECONDS,
) -> float | None:
    if len(samples) < 2:
        return None
    window_start = now - window_seconds
    inside = [sample for sample in samples if sample[0] >= window_start]
    if len(inside) < 2:
        inside = samples[-2:]
    earliest, latest = inside[0], inside[-1]
    elapsed = latest[0] - earliest[0]
    if elapsed <= 0:
        return None
    return (latest[1] - earliest[1]) / elapsed


def progress_ratio(bytes_transferred: int, total_bytes: int | None) -> float | None:
    if total_bytes is None or total_bytes <= 0:
        return None
    return min(1.0, bytes_transferred / total_bytes)
