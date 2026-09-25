from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any
from uuid import UUID

from astroimage.sources.model import SourceDetectionResult
from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    PointDetectionConfigSchema,
)


class DetectionCache:
    def __init__(self, max_entries: int = 256) -> None:
        self._max_entries = max_entries
        self._entries: OrderedDict[str, SourceDetectionResult] = OrderedDict()

    def get(self, key: str) -> SourceDetectionResult | None:
        result = self._entries.get(key)
        if result is not None:
            self._entries.move_to_end(key)
        return result

    def set(self, key: str, result: SourceDetectionResult) -> None:
        self._entries[key] = result
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()


def detection_cache_key(
    *,
    record_id: UUID,
    client_id: str,
    hdu_index: int | None,
    config: PointDetectionConfigSchema,
    extended_config: ExtendedDetectionConfigSchema,
) -> str:
    payload: dict[str, Any] = {
        "record_id": str(record_id),
        "client_id": client_id,
        "hdu": hdu_index,
        "config": config.model_dump(mode="json"),
        "extended_config": extended_config.model_dump(mode="json"),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
