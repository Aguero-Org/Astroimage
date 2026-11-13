from typing import Annotated

from fastapi import Depends

from astroimage.fits.deps import fits_service_dependency
from astroimage.fits.service import FitsService
from astroimage.shared.deps import Settings, settings_dependency
from astroimage.simbad.cache import SimbadReferenceCache
from astroimage.simbad.provider import AstroquerySimbadProvider, SimbadCatalogProvider
from astroimage.simbad.service import SimbadReferenceService
from astroimage.sources.deps import source_service_dependency
from astroimage.sources.service import SourceDetectionService

_simbad_cache = SimbadReferenceCache()


def simbad_provider_dependency(
    settings: Annotated[Settings, Depends(settings_dependency)],
) -> SimbadCatalogProvider:
    return AstroquerySimbadProvider(servers=settings.simbad_servers)


def simbad_reference_service_dependency(
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
    detection: Annotated[SourceDetectionService, Depends(source_service_dependency)],
    provider: Annotated[SimbadCatalogProvider, Depends(simbad_provider_dependency)],
) -> SimbadReferenceService:
    return SimbadReferenceService(
        fits=fits,
        detection=detection,
        provider=provider,
        cache=_simbad_cache,
    )
