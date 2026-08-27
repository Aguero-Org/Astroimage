from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from astroimage.main import app


@pytest.fixture
def asgi_app() -> FastAPI:
    return app


@pytest.fixture
async def client(asgi_app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=asgi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
