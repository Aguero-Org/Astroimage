from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable

from astroimage.shared.errors import AppError, as_app_error
from astroimage.shared.logging import jobs_log as _log


class JobRegistry[ResultT]:
    """Deduplicated background jobs with a bounded result cache.

    Starting the same key twice reuses the running job. Completed results and
    failures are cached with an LRU bound so a poll can still answer after the
    worker finished.
    """

    def __init__(
        self,
        *,
        job_kind: str,
        max_failures: int = 128,
        max_jobs: int = 256,
    ) -> None:
        self._job_kind = job_kind
        self._max_jobs = max_jobs
        self._max_failures = max_failures
        self._done: OrderedDict[str, ResultT] = OrderedDict()
        self._failed: OrderedDict[str, AppError] = OrderedDict()
        self._running: dict[str, asyncio.Task[None]] = {}

    def discard(self, key: str) -> None:
        self._done.pop(key, None)
        self._failed.pop(key, None)

    def get(self, key: str) -> ResultT | None:
        result = self._done.get(key)
        if result is not None:
            self._done.move_to_end(key)
        return result

    def get_failure(self, key: str) -> AppError | None:
        return self._failed.get(key)

    def is_running(self, key: str) -> bool:
        return key in self._running

    async def wait(self, key: str) -> None:
        task = self._running.get(key)
        if task is None or task.done():
            return
        await asyncio.shield(task)

    def start(self, key: str, factory: Callable[[], Awaitable[ResultT]]) -> None:
        if key in self._done or key in self._running:
            return
        self._failed.pop(key, None)
        task = asyncio.create_task(self._execute(key, factory))
        self._running[key] = task

    async def _execute(
        self,
        key: str,
        factory: Callable[[], Awaitable[ResultT]],
    ) -> None:
        try:
            result = await factory()
        except Exception as exc:
            error = as_app_error(exc)
            details = {
                "job_kind": self._job_kind,
                "job_id": key,
                "error_type": type(error).__name__,
                "detail": error.message,
            }
            event = f"{self._job_kind}_job_failed"
            if error.log_level == "warning":
                _log.warning(event, **details, exc_info=exc)
            else:
                _log.error(event, **details, exc_info=exc)
            self._store_failure(key, error)
            return
        finally:
            self._running.pop(key, None)
        _log.info(
            f"{self._job_kind}_job_completed",
            job_kind=self._job_kind,
            job_id=key,
        )
        self._store_done(key, result)

    def _store_done(self, key: str, result: ResultT) -> None:
        self._done[key] = result
        self._done.move_to_end(key)
        self._failed.pop(key, None)
        while len(self._done) > self._max_jobs:
            self._done.popitem(last=False)

    def _store_failure(self, key: str, error: AppError) -> None:
        self._failed[key] = error
        self._failed.move_to_end(key)
        while len(self._failed) > self._max_failures:
            self._failed.popitem(last=False)

    def clear(self) -> None:
        self._done.clear()
        self._failed.clear()
        self._running.clear()
