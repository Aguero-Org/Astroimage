from __future__ import annotations

import asyncio
import threading
from typing import Self

from astroimage.shared.background import BackgroundTasks


class _OpenSpan:
    def __init__(self) -> None:
        self.open = False

    async def __aenter__(self) -> Self:
        self.open = True
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.open = False


async def test_aclose_releases_the_worker_before_returning() -> None:
    tasks = BackgroundTasks()
    entered = threading.Event()
    span = _OpenSpan()

    def block_until_released() -> None:
        entered.set()
        threading.Event().wait(timeout=2)

    async def worker() -> None:
        async with span:
            await asyncio.to_thread(block_until_released)

    assert tasks.start("preview", worker)
    assert await asyncio.to_thread(entered.wait, 2)
    await asyncio.wait_for(tasks.aclose(), timeout=3)
    assert not span.open
    assert not tasks.is_running("preview")


async def test_aclose_finishes_when_the_worker_is_cancelled_during_a_wait() -> None:
    tasks = BackgroundTasks()
    started = asyncio.Event()
    cleaned = asyncio.Event()

    async def worker() -> None:
        started.set()
        try:
            await asyncio.sleep(60)
        finally:
            cleaned.set()

    assert tasks.start("backfill", worker)
    await started.wait()
    await tasks.aclose()
    assert cleaned.is_set()
    assert not tasks.is_running("backfill")
