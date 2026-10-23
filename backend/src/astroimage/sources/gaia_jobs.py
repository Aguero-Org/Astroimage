from __future__ import annotations

import json
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from astroimage.fits.service import FitsService
from astroimage.shared.jobs import JobRegistry
from astroimage.sources.cache import DetectionCache, detection_cache_key
from astroimage.sources.gaia import GaiaCatalogProvider
from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    GaiaMatchConfigSchema,
    GaiaVerificationResponse,
    PointDetectionConfigSchema,
)
from astroimage.sources.service import GaiaVerificationService, SourceDetectionService


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


class GaiaJobRegistry(JobRegistry[GaiaVerificationResponse]):
    def __init__(self, *, max_failures: int = 128, max_jobs: int = 256) -> None:
        super().__init__(
            job_kind="gaia",
            max_failures=max_failures,
            max_jobs=max_jobs,
        )
