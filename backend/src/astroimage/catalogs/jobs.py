from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from astroimage.catalogs.cache import CatalogRecommendationCache
from astroimage.catalogs.readme import ReadmeFetcher
from astroimage.catalogs.schema import (
    CatalogRecommendationConfigSchema,
    CatalogRecommendationResponse,
)
from astroimage.catalogs.service import CatalogRecommendationService
from astroimage.catalogs.vizier import VizierCatalogProvider
from astroimage.fits.service import FitsService
from astroimage.shared.errors import AppError, as_app_error
from astroimage.sources.cache import DetectionCache
from astroimage.sources.service import SourceDetectionService

logger = structlog.get_logger("astroimage.catalogs.jobs")


class CatalogBackgroundRecommend:
    """Runs catalog recommendation with its own resources, safe after the request."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        fit_factory: Callable[[AsyncSession], FitsService],
        provider: VizierCatalogProvider,
        readme_fetcher: ReadmeFetcher,
        cache: CatalogRecommendationCache,
        detection_cache: DetectionCache,
        query_timeout_s: float = 180.0,
    ) -> None:
        self._session_factory = session_factory
        self._fit_factory = fit_factory
        self._provider = provider
        self._readme_fetcher = readme_fetcher
        self._cache = cache
        self._detection_cache = detection_cache
        self._query_timeout_s = query_timeout_s

    async def __call__(
        self,
        record_id: UUID,
        *,
        client_id: str,
        hdu_index: int | None,
        config: CatalogRecommendationConfigSchema,
    ) -> CatalogRecommendationResponse:
        async with self._session_factory() as session:
            fits = self._fit_factory(session)
            detection = SourceDetectionService(fits=fits, cache=self._detection_cache)
            service = CatalogRecommendationService(
                fits=fits,
                detection=detection,
                provider=self._provider,
                readme_fetcher=self._readme_fetcher,
                cache=self._cache,
                query_timeout_s=self._query_timeout_s,
            )
            try:
                result = await service.recommend_from_record(
                    record_id,
                    client_id=client_id,
                    hdu_index=hdu_index,
                    config=config,
                )
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


class CatalogJobRegistry:
    def __init__(self, *, max_failures: int = 128, max_jobs: int = 256) -> None:
        self._max_jobs = max_jobs
        self._max_failures = max_failures
        self._done: OrderedDict[str, CatalogRecommendationResponse] = OrderedDict()
        self._failed: OrderedDict[str, AppError] = OrderedDict()
        self._running: dict[str, asyncio.Task[None]] = {}

    def get(self, key: str) -> CatalogRecommendationResponse | None:
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

    def start(
        self,
        key: str,
        factory: Callable[[], Awaitable[CatalogRecommendationResponse]],
    ) -> None:
        if key in self._done or key in self._running:
            return
        self._failed.pop(key, None)
        task = asyncio.create_task(self._execute(key, factory))
        self._running[key] = task

    async def _execute(
        self,
        key: str,
        factory: Callable[[], Awaitable[CatalogRecommendationResponse]],
    ) -> None:
        try:
            result = await factory()
        except Exception as exc:
            error = as_app_error(exc)
            if error.log_level == "warning":
                logger.warning(
                    "catalog_job_failed",
                    job_id=key,
                    error_type=type(error).__name__,
                    detail=error.message,
                    exc_info=exc,
                )
            else:
                logger.error(
                    "catalog_job_failed",
                    job_id=key,
                    error_type=type(error).__name__,
                    detail=error.message,
                    exc_info=exc,
                )
            self._store_failure(key, error)
            return
        finally:
            self._running.pop(key, None)
        logger.info("catalog_job_completed", job_id=key)
        self._store_done(key, result)

    def _store_done(self, key: str, result: CatalogRecommendationResponse) -> None:
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
