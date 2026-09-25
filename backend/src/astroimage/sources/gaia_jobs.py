from __future__ import annotations

import asyncio
import json
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from astroimage.fits.service import FitsService
from astroimage.sources.cache import DetectionCache, detection_cache_key
from astroimage.sources.gaia import GaiaCatalogProvider
from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    GaiaMatchConfigSchema,
    GaiaVerificationResponse,
    PointDetectionConfigSchema,
)
from astroimage.sources.service import GaiaVerificationService, SourceDetectionService

_log = structlog.get_logger("astroimage.sources.gaia_jobs")


def gaia_job_key(
    *,
    record_id: UUID,
    client_id: str,
    hdu_index: int | None,
    config: PointDetectionConfigSchema,
    extended_config: ExtendedDetectionConfigSchema,
    gaia_config: GaiaMatchConfigSchema,
) -> str:
    detection = detection_cache_key(
        record_id=record_id,
        client_id=client_id,
        hdu_index=hdu_index,
        config=config,
        extended_config=extended_config,
    )
    gaia_payload = json.dumps(
        gaia_config.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return f"{detection}|gaia:{gaia_payload}"


class GaiaBackgroundVerify:
    """Runs gaia verification with its own resources, safe after the request ends."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        fit_factory: Callable[[AsyncSession], FitsService],
        provider: GaiaCatalogProvider,
        cache: DetectionCache,
        query_timeout_s: float = 120.0,
    ) -> None:
        self._session_factory = session_factory
        self._fit_factory = fit_factory
        self._provider = provider
        self._cache = cache
        self._query_timeout_s = query_timeout_s

    async def __call__(
        self,
        record_id: UUID,
        *,
        client_id: str,
        hdu_index: int | None,
        config: PointDetectionConfigSchema,
        extended_config: ExtendedDetectionConfigSchema,
        gaia_config: GaiaMatchConfigSchema,
    ) -> GaiaVerificationResponse:
        async with self._session_factory() as session:
            fits = self._fit_factory(session)
            detection = SourceDetectionService(fits=fits, cache=self._cache)
            service = GaiaVerificationService(
                detection,
                fits=fits,
                provider=self._provider,
                query_timeout_s=self._query_timeout_s,
            )
            try:
                result = await service.verify_from_record(
                    record_id,
                    client_id=client_id,
                    hdu_index=hdu_index,
                    config=config,
                    extended_config=extended_config,
                    gaia_config=gaia_config,
                )
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


class GaiaJobRegistry:
    def __init__(self, *, max_failures: int = 128, max_jobs: int = 256) -> None:
        self._max_jobs = max_jobs
        self._max_failures = max_failures
        self._done: OrderedDict[str, GaiaVerificationResponse] = OrderedDict()
        self._failed: OrderedDict[str, tuple[int, str]] = OrderedDict()
        self._running: dict[str, asyncio.Task[None]] = {}

    def get(self, key: str) -> GaiaVerificationResponse | None:
        result = self._done.get(key)
        if result is not None:
            self._done.move_to_end(key)
        return result

    def get_failure(self, key: str) -> tuple[int, str] | None:
        return self._failed.get(key)

    def is_running(self, key: str) -> bool:
        return key in self._running

    async def wait(self, key: str) -> None:
        task = self._running.get(key)
        if task is None or task.done():
            return
        await asyncio.shield(task)

    def start(
        self,
        key: str,
        factory: Callable[[], Awaitable[GaiaVerificationResponse]],
    ) -> None:
        if key in self._done or key in self._running:
            return
        self._failed.pop(key, None)
        task = asyncio.create_task(self._execute(key, factory))
        self._running[key] = task

    async def _execute(
        self,
        key: str,
        factory: Callable[[], Awaitable[GaiaVerificationResponse]],
    ) -> None:
        try:
            try:
                result = await factory()
            except LookupError as exc:
                self._store_failure(key, 404, str(exc))
                return
            except (ValueError, OSError) as exc:
                self._store_failure(key, 400, str(exc))
                return
            except Exception as exc:
                _log.exception("gaia_job_failed", job_id=key, detail=str(exc))
                self._store_failure(key, 500, str(exc))
                return
        finally:
            self._running.pop(key, None)
        _log.info("gaia_job_completed", job_id=key)
        self._store_done(key, result)

    def _store_done(self, key: str, result: GaiaVerificationResponse) -> None:
        self._done[key] = result
        self._done.move_to_end(key)
        self._failed.pop(key, None)
        while len(self._done) > self._max_jobs:
            self._done.popitem(last=False)

    def _store_failure(self, key: str, status_code: int, detail: str) -> None:
        self._failed[key] = (status_code, detail)
        self._failed.move_to_end(key)
        while len(self._failed) > self._max_failures:
            self._failed.popitem(last=False)

    def clear(self) -> None:
        self._done.clear()
        self._failed.clear()
        self._running.clear()
