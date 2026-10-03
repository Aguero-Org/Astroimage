from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID, uuid4

import pytest

from astroimage.shared.errors import (
    BadRequestError,
    InternalServerError,
    NotFoundError,
)
from astroimage.sources.gaia_jobs import GaiaJobRegistry, gaia_job_key
from astroimage.sources.schema import (
    ExtendedDetectionConfigSchema,
    GaiaMatchConfigSchema,
    GaiaVerificationResponse,
    PointDetectionConfigSchema,
)


def _params(
    *,
    record_id: UUID | None = None,
    gaia_config: GaiaMatchConfigSchema | None = None,
    client_id: str = "alice",
) -> dict[str, Any]:
    return {
        "record_id": record_id or uuid4(),
        "client_id": client_id,
        "hdu_index": None,
        "config": PointDetectionConfigSchema(),
        "extended_config": ExtendedDetectionConfigSchema(),
        "gaia_config": gaia_config or GaiaMatchConfigSchema(),
    }


def _success_response() -> GaiaVerificationResponse:
    return GaiaVerificationResponse(
        match_radius_arcsec=4.0,
        probability_power=2.0,
        queried=True,
    )


async def _success_coro() -> GaiaVerificationResponse:
    return _success_response()


def test_gaia_job_key_is_deterministic() -> None:
    params = _params()

    assert gaia_job_key(**params) == gaia_job_key(**params)


def test_gaia_job_key_varies_by_gaia_config_and_client() -> None:
    record_id = uuid4()
    base = _params(record_id=record_id)
    wider = _params(record_id=record_id, gaia_config=GaiaMatchConfigSchema(match_radius_arcsec=8.0))
    other_client = _params(record_id=record_id, client_id="bob")

    assert gaia_job_key(**base) != gaia_job_key(**wider)
    assert gaia_job_key(**base) != gaia_job_key(**other_client)


@pytest.mark.asyncio
async def test_registry_returns_completed_result() -> None:
    registry = GaiaJobRegistry()

    async def factory() -> GaiaVerificationResponse:
        return _success_response()

    registry.start("key", factory)
    await registry.wait("key")

    assert registry.get("key") == _success_response()
    assert registry.is_running("key") is False


@pytest.mark.asyncio
async def test_registry_deduplicates_running_jobs() -> None:
    registry = GaiaJobRegistry()
    calls = 0
    started = asyncio.Event()
    release = asyncio.Event()

    async def factory() -> GaiaVerificationResponse:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return _success_response()

    registry.start("key", factory)
    await started.wait()
    registry.start("key", factory)

    assert calls == 1

    release.set()
    await registry.wait("key")


@pytest.mark.asyncio
async def test_registry_records_failures_by_exception_type() -> None:
    registry = GaiaJobRegistry()

    async def value_failure() -> GaiaVerificationResponse:
        raise ValueError("boom")

    async def lookup_failure() -> GaiaVerificationResponse:
        raise LookupError("missing")

    async def runtime_failure() -> GaiaVerificationResponse:
        raise RuntimeError("surprise")

    registry.start("val", value_failure)
    registry.start("lookup", lookup_failure)
    registry.start("runtime", runtime_failure)
    await registry.wait("val")
    await registry.wait("lookup")
    await registry.wait("runtime")

    value_failure_result = registry.get_failure("val")
    assert isinstance(value_failure_result, BadRequestError)
    assert value_failure_result.status_code == 400
    assert value_failure_result.message == "boom"
    lookup_failure_result = registry.get_failure("lookup")
    assert isinstance(lookup_failure_result, NotFoundError)
    assert lookup_failure_result.status_code == 404
    assert lookup_failure_result.message == "missing"
    runtime_failure_result = registry.get_failure("runtime")
    assert isinstance(runtime_failure_result, InternalServerError)
    assert runtime_failure_result.status_code == 500
    assert registry.get("val") is None


@pytest.mark.asyncio
async def test_registry_evicts_oldest_completed_jobs() -> None:
    registry = GaiaJobRegistry(max_jobs=2)

    for key in ("a", "b", "c"):
        registry.start(key, _success_coro)
        await registry.wait(key)

    assert registry.get("a") is None
    assert registry.get("b") == _success_response()
    assert registry.get("c") == _success_response()


@pytest.mark.asyncio
async def test_registry_restarts_after_failure() -> None:
    registry = GaiaJobRegistry()
    attempts = 0

    async def factory() -> GaiaVerificationResponse:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ValueError("first attempt fails")
        return _success_response()

    registry.start("key", factory)
    await registry.wait("key")
    retry_failure = registry.get_failure("key")
    assert isinstance(retry_failure, BadRequestError)
    assert retry_failure.status_code == 400
    assert retry_failure.message == "first attempt fails"

    registry.start("key", factory)
    await registry.wait("key")
    assert registry.get("key") == _success_response()
    assert registry.get_failure("key") is None
