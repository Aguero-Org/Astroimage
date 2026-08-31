from __future__ import annotations

import os
from collections.abc import AsyncIterator

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://astroimage:astroimage@localhost:5432/astroimage",
)
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("MINIO_BUCKET", "astroimage-test")
os.environ.setdefault("MINIO_SECURE", "false")

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from astroimage.config import get_settings
from astroimage.main import app

get_settings.cache_clear()


@pytest.fixture
def asgi_app() -> FastAPI:
    return app


@pytest.fixture
async def client(asgi_app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with asgi_app.router.lifespan_context(asgi_app):
        transport = ASGITransport(app=asgi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
