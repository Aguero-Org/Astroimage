from __future__ import annotations

import os
from collections.abc import AsyncIterator

# Provide a credential-free URL for tests before the app loads settings.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://localhost:5432/astroimage",
)

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
    transport = ASGITransport(app=asgi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
