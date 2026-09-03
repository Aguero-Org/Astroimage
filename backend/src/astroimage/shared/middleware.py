import json
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from astroimage.shared.telemetry import current_trace_ids

logger = structlog.get_logger("astroimage.http")

_BINARY_CONTENT_TYPES = (
    "image/",
    "application/octet-stream",
    "application/zip",
    "audio/",
    "video/",
)


def _is_binary(content_type: str) -> bool:
    return content_type.startswith(_BINARY_CONTENT_TYPES)


def _decode_body(body: bytes, content_type: str) -> Any:
    if _is_binary(content_type):
        return None
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError:
        return body.decode("utf-8", errors="replace")


def _response_bytes(response: Response) -> tuple[bytes, bool]:
    if isinstance(response, StreamingResponse):
        return b"", True
    body = getattr(response, "body", b"")
    return (body if isinstance(body, bytes) else b""), False


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        settings = getattr(request.app.state, "settings", None)
        service_name = getattr(settings, "app_name", None)
        structlog.contextvars.clear_contextvars()
        context: dict[str, str] = {"request_id": request_id}
        if isinstance(service_name, str) and service_name:
            context["service_name"] = service_name
        structlog.contextvars.bind_contextvars(**context)

        request_body = b""
        if request.method in {"POST", "PUT", "PATCH"}:
            request_body = await request.body()
            request._body = request_body

        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        response_content_type = response.headers.get("content-type", "")
        response_body, streaming = _response_bytes(response)
        response_body_bytes = None if streaming else len(response_body)

        response.headers["x-request-id"] = request_id
        trace_id, span_id = current_trace_ids()
        if trace_id is not None:
            structlog.contextvars.bind_contextvars(trace_id=trace_id)
        if span_id is not None:
            structlog.contextvars.bind_contextvars(span_id=span_id)

        request_content_type = request.headers.get("content-type", "")
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=latency_ms,
            request_id=request_id,
            service_name=service_name,
            trace_id=trace_id,
            span_id=span_id,
            request_body=_decode_body(request_body, request_content_type),
            request_body_bytes=len(request_body),
            response_body=_decode_body(response_body, response_content_type),
            response_body_bytes=response_body_bytes,
        )

        return response
