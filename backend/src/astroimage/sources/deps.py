from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.deps import fits_service_dependency, fits_service_from_resources
from astroimage.fits.service import FitsService
from astroimage.shared.deps import object_storage_dependency
from astroimage.shared.object_storage import ObjectStorage
from astroimage.sources.cache import DetectionCache
from astroimage.sources.gaia import AstroqueryGaiaProvider, GaiaCatalogProvider
from astroimage.sources.gaia_jobs import GaiaBackgroundVerify, GaiaJobRegistry
from astroimage.sources.service import GaiaVerificationService, SourceDetectionService

_detection_cache = DetectionCache()
_gaia_jobs = GaiaJobRegistry()


def source_service_dependency(
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
) -> SourceDetectionService:
    return SourceDetectionService(fits=fits, cache=_detection_cache)


def gaia_provider_dependency() -> GaiaCatalogProvider:
    return AstroqueryGaiaProvider()


def gaia_service_dependency(
    service: Annotated[SourceDetectionService, Depends(source_service_dependency)],
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
    provider: Annotated[GaiaCatalogProvider, Depends(gaia_provider_dependency)],
) -> GaiaVerificationService:
    return GaiaVerificationService(service, fits=fits, provider=provider)


def _fit_factory(objects: ObjectStorage) -> Callable[[AsyncSession], FitsService]:
    return lambda session: fits_service_from_resources(session, objects)


def gaia_background_dependency(
    service: Annotated[GaiaVerificationService, Depends(gaia_service_dependency)],
    request: Request,
) -> GaiaBackgroundVerify:
    settings = request.app.state.settings
    objects = object_storage_dependency(request.app.state.minio_client, settings)
    return GaiaBackgroundVerify(
        session_factory=request.app.state.session_factory,
        fit_factory=_fit_factory(objects),
        provider=service.provider,
        cache=_detection_cache,
    )


def gaia_job_registry_dependency() -> GaiaJobRegistry:
    return _gaia_jobs
