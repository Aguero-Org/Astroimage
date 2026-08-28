import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint_is_exposed(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests" in response.text or "python_info" in response.text
