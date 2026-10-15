from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.catalogs.cache import CatalogRecommendationCache
from astroimage.catalogs.jobs import CatalogBackgroundRecommend, CatalogJobRegistry
from astroimage.catalogs.readme import CdsReadmeFetcher, ReadmeFetcher
from astroimage.catalogs.service import CatalogRecommendationService
from astroimage.catalogs.vizier import AstroqueryVizierProvider, VizierCatalogProvider
from astroimage.fits.deps import fits_service_dependency, fits_service_from_resources
from astroimage.fits.service import FitsService
from astroimage.shared.deps import object_storage_dependency
from astroimage.shared.object_storage import ObjectStorage
from astroimage.sources.cache import DetectionCache
from astroimage.sources.deps import source_service_dependency
from astroimage.sources.service import SourceDetectionService

_recommendation_cache = CatalogRecommendationCache()
_catalog_jobs = CatalogJobRegistry()
_detection_cache = DetectionCache()


def vizier_provider_dependency() -> VizierCatalogProvider:
    return AstroqueryVizierProvider()


def readme_fetcher_dependency() -> ReadmeFetcher:
    return CdsReadmeFetcher()


def catalog_recommendation_service_dependency(
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
    detection: Annotated[SourceDetectionService, Depends(source_service_dependency)],
    provider: Annotated[VizierCatalogProvider, Depends(vizier_provider_dependency)],
    readme: Annotated[ReadmeFetcher, Depends(readme_fetcher_dependency)],
) -> CatalogRecommendationService:
    return CatalogRecommendationService(
        fits=fits,
        detection=detection,
        provider=provider,
        readme_fetcher=readme,
        cache=_recommendation_cache,
    )


def _fit_factory(objects: ObjectStorage) -> Callable[[AsyncSession], FitsService]:
    return lambda session: fits_service_from_resources(session, objects)


def catalog_background_dependency(
    provider: Annotated[VizierCatalogProvider, Depends(vizier_provider_dependency)],
    readme: Annotated[ReadmeFetcher, Depends(readme_fetcher_dependency)],
    request: Request,
) -> CatalogBackgroundRecommend:
    settings = request.app.state.settings
    objects = object_storage_dependency(request.app.state.minio_client, settings)
    return CatalogBackgroundRecommend(
        session_factory=request.app.state.session_factory,
        fit_factory=_fit_factory(objects),
        provider=provider,
        readme_fetcher=readme,
        cache=_recommendation_cache,
        detection_cache=_detection_cache,
    )


def catalog_job_registry_dependency() -> CatalogJobRegistry:
    return _catalog_jobs
