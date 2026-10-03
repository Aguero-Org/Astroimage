from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from astroimage.sources.model import SourceDetectionResult
from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    PointDetectionConfigSchema,
)


@dataclass(frozen=True)
class CachedDetection:
    """A detection plus the configuration that produced it.

    The preset endpoint needs both: the sources to measure the PSF on, and the
    parameters the user already chose, so it can rescale instead of overwrite.
    """

    result: SourceDetectionResult
    point_config: PointDetectionConfigSchema
    extended_config: ExtendedDetectionConfigSchema


class DetectionCache:
    def __init__(self, max_entries: int = 256) -> None:
        self._max_entries = max_entries
        self._entries: OrderedDict[str, CachedDetection] = OrderedDict()
        self._scopes: OrderedDict[str, str] = OrderedDict()

    def get(self, key: str) -> CachedDetection | None:
        entry = self._entries.get(key)
        if entry is not None:
            self._entries.move_to_end(key)
        return entry

    def get_latest(self, scope: str) -> CachedDetection | None:
        """Most recent detection for a record/client/hdu, whatever its parameters."""
        key = self._scopes.get(scope)
        if key is None:
            return None
        entry = self.get(key)
        if entry is None:
            self._scopes.pop(scope, None)
            return None
        self._scopes.move_to_end(scope)
        return entry

    def set(self, key: str, entry: CachedDetection, *, scope: str) -> None:
        self._entries[key] = entry
        self._entries.move_to_end(key)
        self._scopes[scope] = key
        self._scopes.move_to_end(scope)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)
        while len(self._scopes) > self._max_entries:
            self._scopes.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()
        self._scopes.clear()


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


def detection_scope_key(
    *,
    record_id: UUID,
    client_id: str,
    hdu_index: int | None,
) -> str:
    """Identity of an image for one client, independent of detection parameters."""
    payload: dict[str, Any] = {
        "record_id": str(record_id),
        "client_id": client_id,
        "hdu": hdu_index,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
