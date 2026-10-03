from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi import FastAPI, Query
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from astroimage.shared.errors import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    UnauthorizedError,
    UpstreamServiceError,
    register_exception_handlers,
)

INTERNAL_ERROR_MESSAGE = "Internal server error"


class _Body(BaseModel):
    name: str


@pytest.fixture
def error_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/app-error/{status}")
    async def raise_app_error(status: int) -> None:
        raise {
            400: BadRequestError,
            401: UnauthorizedError,
            403: ForbiddenError,
            404: NotFoundError,
            409: ConflictError,
            500: InternalServerError,
            502: UpstreamServiceError,
        }[status](f"boom-{status}")

    @app.get("/lookup-error")
    async def raise_lookup_error() -> None:
        raise LookupError("missing record")

    @app.get("/value-error")
    async def raise_value_error() -> None:
        raise ValueError("invalid value")

    @app.get("/os-error")
    async def raise_os_error() -> None:
        raise OSError("unreadable file")

    @app.get("/unknown-error")
    async def raise_unknown_error() -> None:
        raise RuntimeError("internal database url leaked here")

    @app.get("/sync-error")
    def raise_sync_error() -> None:
        raise ValueError("sync endpoint failure")

    @app.get("/ok")
    async def ok() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/body")
    async def echo(body: _Body, limit: int = Query(10)) -> _Body:
        return body

    return app


@pytest.fixture
async def error_client(error_app: FastAPI) -> AsyncIterator[AsyncClient]:
    # raise_app_exceptions=False: ServerErrorMiddleware re-raises after responding,
    # so the generic 500 can only be observed through the transport.
    transport = ASGITransport(app=error_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.parametrize(
    "status",
    [400, 401, 403, 404, 409, 500, 502],
)
@pytest.mark.asyncio
async def test_app_error_status_and_detail(
    error_client: AsyncClient,
    status: int,
) -> None:
    response = await error_client.get(f"/app-error/{status}")
    assert response.status_code == status
    assert response.json() == {"detail": f"boom-{status}"}


@pytest.mark.asyncio
async def test_lookup_error_becomes_404(error_client: AsyncClient) -> None:
    response = await error_client.get("/lookup-error")
    assert response.status_code == 404
    assert response.json() == {"detail": "missing record"}


@pytest.mark.asyncio
async def test_value_error_becomes_400(error_client: AsyncClient) -> None:
    response = await error_client.get("/value-error")
    assert response.status_code == 400
    assert response.json() == {"detail": "invalid value"}


@pytest.mark.asyncio
async def test_os_error_becomes_400(error_client: AsyncClient) -> None:
    response = await error_client.get("/os-error")
    assert response.status_code == 400
    assert response.json() == {"detail": "unreadable file"}


@pytest.mark.asyncio
async def test_sync_endpoint_error_is_translated(error_client: AsyncClient) -> None:
    response = await error_client.get("/sync-error")
    assert response.status_code == 400
    assert response.json() == {"detail": "sync endpoint failure"}


@pytest.mark.asyncio
async def test_unknown_error_returns_generic_500(error_client: AsyncClient) -> None:
    response = await error_client.get("/unknown-error")
    assert response.status_code == 500
    assert response.json() == {"detail": INTERNAL_ERROR_MESSAGE}
    assert "internal database url leaked here" not in response.text


@pytest.mark.asyncio
async def test_successful_request_is_untouched(error_client: AsyncClient) -> None:
    response = await error_client.get("/ok")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_validation_errors_keep_fastapi_contract(error_client: AsyncClient) -> None:
    response = await error_client.post("/body", json={"name": 1})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert detail[0]["loc"] == ["body", "name"]


@pytest.mark.asyncio
async def test_valid_body_still_validates(error_client: AsyncClient) -> None:
    response = await error_client.post("/body", json={"name": "ok"})
    assert response.status_code == 200
    assert response.json() == {"name": "ok"}


@pytest.mark.asyncio
async def test_response_keeps_error_content_type(error_client: AsyncClient) -> None:
    response = await error_client.get("/lookup-error")
    assert response.headers["content-type"].startswith("application/json")


@pytest.fixture
def broken_logger(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """A logger that always raises, to prove logging cannot break the response."""
    from astroimage.shared import errors

    class _ExplodingLogger:
        def __getattr__(self, _name: str) -> object:
            def _raise(*_args: object, **_kwargs: object) -> None:
                raise RuntimeError("logger backend down")

            return _raise

    monkeypatch.setattr(
        errors, "_LOGS", {"warning": _ExplodingLogger(), "error": _ExplodingLogger()}
    )
    yield


@pytest.mark.asyncio
async def test_logging_failure_still_returns_error_response(
    error_app: FastAPI,
    broken_logger: None,
) -> None:
    transport = ASGITransport(app=error_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        crashed = await client.get("/unknown-error")
        assert crashed.status_code == 500
        assert crashed.json() == {"detail": INTERNAL_ERROR_MESSAGE}
        not_found = await client.get("/lookup-error")
        assert not_found.status_code == 404
        assert not_found.json() == {"detail": "missing record"}
