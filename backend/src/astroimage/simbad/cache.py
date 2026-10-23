from __future__ import annotations

import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from astroimage.simbad.schema import SimbadReferencesConfigSchema, SimbadReferencesResponse


@dataclass(frozen=True)
class CachedSimbadReferences:
    result: SimbadReferencesResponse
    created_at: float


class SimbadReferenceCache:
    def __init__(self, *, max_entries: int = 128, ttl_s: float = 3600.0) -> None:
        self._max_entries = max_entries
        self._ttl_s = ttl_s
        self._entries: OrderedDict[str, CachedSimbadReferences] = OrderedDict()

    def get(self, key: str) -> SimbadReferencesResponse | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if time.time() - entry.created_at > self._ttl_s:
            self._entries.pop(key, None)
            return None
        self._entries.move_to_end(key)
        return entry.result

    def set(self, key: str, result: SimbadReferencesResponse) -> None:
        self._entries[key] = CachedSimbadReferences(result=result, created_at=time.time())
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()


def simbad_cache_key(
    *,
    record_id: UUID,
    client_id: str,
    hdu_index: int | None,
    config: SimbadReferencesConfigSchema,
) -> str:
    payload: dict[str, Any] = {
        "record_id": str(record_id),
        "client_id": client_id,
        "hdu": hdu_index,
        "config": config.model_dump(mode="json"),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
