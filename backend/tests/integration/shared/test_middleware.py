import pytest
from httpx import AsyncClient
from structlog.testing import capture_logs


@pytest.mark.asyncio
async def test_request_log_includes_otel_trace_id(client: AsyncClient) -> None:
    with capture_logs() as captured:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    request_logs = [entry for entry in captured if entry.get("event") == "request"]
    assert request_logs
    log_entry = request_logs[-1]
    assert log_entry.get("service_name") == "astroimage"
    assert log_entry.get("request_id")
    trace_id = log_entry.get("trace_id")
    assert isinstance(trace_id, str)
    assert len(trace_id) == 32
    assert int(trace_id, 16) != 0
