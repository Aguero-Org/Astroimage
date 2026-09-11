from typing import Any

import pytest
from fastapi import FastAPI
from sqlalchemy import text
from starlette.requests import Request

from astroimage.config import get_settings
from astroimage.shared.deps import (
    db_session_dependency,
    minio_client_dependency,
    object_storage_dependency,
    settings_dependency,
)


def _http_request(app: FastAPI) -> Request:
    scope: dict[str, Any] = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "app": app,
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_deps_use_live_postgres_and_minio(asgi_app: FastAPI) -> None:
    lifespan = asgi_app.router.lifespan_context
    async with lifespan(asgi_app):
        request = _http_request(asgi_app)
        assert settings_dependency() is get_settings()

        async for session in db_session_dependency(request):
            assert await session.scalar(text("SELECT 1")) == 1
            break

        storage = object_storage_dependency(minio_client_dependency(request), get_settings())
        await storage.put_bytes(
            "shared/deps-check.bin",
            b"ok",
            content_type="application/octet-stream",
        )
        assert await storage.get_bytes("shared/deps-check.bin") == b"ok"
        await storage.remove("shared/deps-check.bin")
