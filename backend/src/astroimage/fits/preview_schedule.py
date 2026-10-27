from __future__ import annotations

from typing import Protocol
from uuid import UUID


class PreviewScheduler(Protocol):
    def schedule(self, record_id: UUID) -> None: ...


class NullPreviewScheduler:
    def schedule(self, record_id: UUID) -> None:
        return None
