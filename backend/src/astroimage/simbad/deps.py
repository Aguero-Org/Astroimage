from typing import Annotated

from fastapi import Depends

from astroimage.catalogs.cone_cache import CatalogConeCache
from astroimage.catalogs.deps import catalog_cone_cache_dependency
from astroimage.fits.deps import fits_service_dependency
from astroimage.fits.service import FitsService
from astroimage.simbad.cache import SimbadReferenceCache
from astroimage.simbad.provider import AstroquerySimbadProvider, SimbadCatalogProvider
from astroimage.simbad.service import SimbadReferenceService
from astroimage.sources.deps import source_service_dependency
from astroimage.sources.service import SourceDetectionService

_simbad_cache = SimbadReferenceCache()


def simbad_provider_dependency() -> SimbadCatalogProvider:
    return AstroquerySimbadProvider()


def simbad_reference_service_dependency(
    fits: Annotated[FitsService, Depends(fits_service_dependency)],
    detection: Annotated[SourceDetectionService, Depends(source_service_dependency)],
    provider: Annotated[SimbadCatalogProvider, Depends(simbad_provider_dependency)],
    downloads: Annotated[CatalogConeCache, Depends(catalog_cone_cache_dependency)],
) -> SimbadReferenceService:
    return SimbadReferenceService(
        fits=fits,
        detection=detection,
        provider=provider,
        cache=_simbad_cache,
        downloads=downloads,
    )
