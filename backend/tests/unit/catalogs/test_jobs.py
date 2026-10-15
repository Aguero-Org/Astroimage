from __future__ import annotations

import asyncio

import pytest

from astroimage.catalogs.jobs import CatalogJobRegistry
from astroimage.catalogs.schema import CatalogRecommendationResponse
from astroimage.shared.errors import InternalServerError


@pytest.mark.asyncio
async def test_registry_runs_and_caches_a_job() -> None:
    registry = CatalogJobRegistry()

    async def factory() -> CatalogRecommendationResponse:
        return CatalogRecommendationResponse(source_name="survey.fits", queried=True)

    registry.start("job", factory)
    assert registry.is_running("job") is True
    await registry.wait("job")
    result = registry.get("job")
    assert result is not None
    assert result.queried is True
    assert registry.is_running("job") is False


@pytest.mark.asyncio
async def test_registry_records_failures() -> None:
    registry = CatalogJobRegistry()

    async def factory() -> CatalogRecommendationResponse:
        raise InternalServerError("boom")

    registry.start("job", factory)
    await registry.wait("job")
    assert registry.get("job") is None
    failure = registry.get_failure("job")
    assert failure is not None
    assert failure.message == "boom"


@pytest.mark.asyncio
async def test_registry_does_not_restart_completed_jobs() -> None:
    registry = CatalogJobRegistry()
    calls = 0

    async def factory() -> CatalogRecommendationResponse:
        nonlocal calls
        calls += 1
        return CatalogRecommendationResponse()

    registry.start("job", factory)
    await registry.wait("job")
    registry.start("job", factory)
    await asyncio.sleep(0)
    assert calls == 1
