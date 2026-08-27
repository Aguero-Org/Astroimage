import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_health_echoes_request_id(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"x-request-id": "test-correlation-id"})
    assert response.headers["x-request-id"] == "test-correlation-id"


@pytest.mark.asyncio
async def test_metrics_endpoint_is_exposed(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests" in response.text or "python_info" in response.text
