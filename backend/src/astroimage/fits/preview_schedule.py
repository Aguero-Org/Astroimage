from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class PreviewScheduler(Protocol):
    def schedule(self, record_id: UUID) -> None: ...


class NullPreviewScheduler:
    def schedule(self, record_id: UUID) -> None:
        del record_id
