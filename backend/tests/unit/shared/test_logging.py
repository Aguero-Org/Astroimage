from __future__ import annotations

import io
import logging
from typing import Any

import structlog

from astroimage.shared.logging import enrich_exceptions, setup_logging


class _FakeUrl:
    host = "vizier.cfa.harvard.edu"


class _FakeRequest:
    url = _FakeUrl()


class _FakeResponse:
    status_code = 404


class _HttpError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.request = _FakeRequest()
        self.response = _FakeResponse()


class _DALServiceError(Exception):
    pass


def _run(event_dict: dict[str, Any]) -> dict[str, Any]:
    return dict(enrich_exceptions(None, "warning", dict(event_dict)))


def test_ignores_events_without_exception() -> None:
    event_dict = {"event": "catalog_download_hit", "level": "info"}
    assert _run(event_dict) == event_dict


def test_classifies_timeout_and_drops_traceback() -> None:
    result = _run(
        {
            "event": "simbad_query_failed",
            "level": "warning",
            "exc_info": TimeoutError("HTTPSConnectionPool: Read timed out. (read timeout=60)"),
        }
    )
    assert result["error_type"] == "TimeoutError"
    assert result["error_kind"] == "timeout"
    assert result["http_status"] is None
    assert "exc_info" not in result


def test_extracts_http_status_and_host() -> None:
    result = _run({"event": "vizier_server_failed", "level": "info", "exc_info": _HttpError("404")})
    assert result["error_kind"] == "http"
    assert result["http_status"] == 404
    assert result["host"] == "vizier.cfa.harvard.edu"


def test_classifies_service_error() -> None:
    result = _run(
        {
            "event": "simbad_query_failed",
            "level": "warning",
            "exc_info": _DALServiceError("Unable to access the capabilities endpoint"),
        }
    )
    assert result["error_kind"] == "service"


def test_accepts_exc_info_tuple() -> None:
    result = _run(
        {"event": "x", "level": "warning", "exc_info": (ValueError, ValueError("boom"), None)}
    )
    assert result["error_type"] == "ValueError"


def test_keeps_traceback_only_at_debug() -> None:
    error = ValueError("boom")
    result = _run({"event": "x", "level": "debug", "exc_info": error})
    assert result["exc_info"] is error
    assert result["error_type"] == "ValueError"


def test_collapses_whitespace_and_truncates_detail() -> None:
    collapsed = _run(
        {"event": "x", "level": "warning", "exc_info": ValueError("line one\n\tline two")}
    )
    assert collapsed["detail"] == "line one line two"

    truncated = _run({"event": "x", "level": "warning", "exc_info": ValueError("x" * 500)})
    detail = truncated["detail"]
    assert isinstance(detail, str)
    assert len(detail) == 300
    assert detail.endswith("…")


def test_keeps_explicit_detail() -> None:
    result = _run(
        {"event": "x", "level": "warning", "exc_info": ValueError("boom"), "detail": "already set"}
    )
    assert result["detail"] == "already set"


def test_configured_logger_omits_the_traceback_outside_debug() -> None:
    setup_logging("INFO")
    stream = io.StringIO()
    handlers = [
        handler
        for handler in logging.getLogger().handlers
        if isinstance(handler, logging.StreamHandler)
    ]
    originals = [handler.stream for handler in handlers]
    for handler in handlers:
        handler.stream = stream
    try:
        logger = structlog.get_logger("boundary")
        try:
            raise ValueError("boom")
        except ValueError:
            logger.exception("probe_failed")
    finally:
        for handler, original in zip(handlers, originals, strict=True):
            handler.stream = original

    output = stream.getvalue()
    assert "probe_failed" in output
    assert "Traceback" not in output
