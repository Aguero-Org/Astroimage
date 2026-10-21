from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

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
from astroimage.shared.jobs import JobRegistry
from astroimage.sources.cache import DetectionCache
from astroimage.sources.service import SourceDetectionService


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


class CatalogJobRegistry(JobRegistry[CatalogRecommendationResponse]):
    def __init__(self, *, max_failures: int = 128, max_jobs: int = 256) -> None:
        super().__init__(
            job_kind="catalog",
            max_failures=max_failures,
            max_jobs=max_jobs,
        )
