from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


class BackgroundTasks:
    """Tracks asyncio tasks that must outlive the HTTP request that started them.

    The registry is an execution handle only. Durable state belongs to the caller.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def is_running(self, key: str) -> bool:
        task = self._tasks.get(key)
        return task is not None and not task.done()

    def start(self, key: str, worker: Callable[[], Awaitable[None]]) -> bool:
        if self.is_running(key):
            return False
        task = asyncio.create_task(self._run(key, worker))
        self._tasks[key] = task
        return True

    def cancel(self, key: str) -> None:
        task = self._tasks.get(key)
        if task is not None and not task.done():
            task.cancel()

    async def _run(self, key: str, worker: Callable[[], Awaitable[None]]) -> None:
        try:
            await worker()
        finally:
            current = self._tasks.get(key)
            if current is asyncio.current_task():
                self._tasks.pop(key, None)

    def clear(self) -> None:
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
        self._tasks.clear()
