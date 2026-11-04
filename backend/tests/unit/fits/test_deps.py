from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from astroimage.fits.deps import preview_scheduler_from_request
from astroimage.fits.preview_schedule import NullPreviewScheduler


def _request(scheduler: object | None) -> SimpleNamespace:
    state = SimpleNamespace()
    if scheduler is not None:
        state.preview_scheduler = scheduler
    return SimpleNamespace(app=SimpleNamespace(state=state))


def test_missing_scheduler_is_a_wiring_error() -> None:
    with pytest.raises(TypeError, match="Preview scheduler is not configured"):
        preview_scheduler_from_request(_request(None))  # type: ignore[arg-type]


def test_configured_scheduler_is_returned() -> None:
    scheduler = NullPreviewScheduler()

    resolved = preview_scheduler_from_request(_request(scheduler))  # type: ignore[arg-type]

    resolved.schedule(uuid4())
    assert resolved is scheduler
