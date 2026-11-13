import logging
import re
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

_OTLP_EXPORTER_LOGGER = "opentelemetry.exporter.otlp.proto.http.trace_exporter"

catalog_jobs_log = structlog.get_logger("astroimage.catalogs.jobs")
catalog_service_log = structlog.get_logger("astroimage.catalogs.service")
catalog_vizier_log = structlog.get_logger("astroimage.catalogs.vizier")
jobs_log = structlog.get_logger("astroimage.shared.jobs")
preview_log = structlog.get_logger("astroimage.render.preview")
simbad_provider_log = structlog.get_logger("astroimage.simbad.provider")
simbad_service_log = structlog.get_logger("astroimage.simbad.service")

_WHITESPACE_RE = re.compile(r"\s+")
_MAX_DETAIL_CHARS = 300


def enrich_exceptions(
    logger: Any,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Turn an attached exception into legible, classified fields.

    Every failure logged through ``_log`` carries the same shape regardless of
    the call site: ``error_type``, ``error_kind``, ``http_status``, ``host`` and a
    single-line ``detail``. The full traceback is dropped outside DEBUG so one
    provider error cannot flood the stream.
    """
    del logger, method_name
    error = _exception_from(event_dict.get("exc_info"))
    if error is None:
        return event_dict
    event_dict["error_type"] = type(error).__name__
    event_dict["error_kind"] = _error_kind(error)
    event_dict["http_status"] = _http_status(error)
    event_dict["host"] = _host(error)
    event_dict.setdefault("detail", _one_line(str(error)))
    if event_dict.get("level") != "debug":
        event_dict.pop("exc_info", None)
    return event_dict


def _exception_from(exc_info: object) -> BaseException | None:
    if isinstance(exc_info, BaseException):
        return exc_info
    if isinstance(exc_info, tuple) and len(exc_info) >= 2:
        candidate = exc_info[1]
        return candidate if isinstance(candidate, BaseException) else None
    if exc_info is not None:
        return sys.exc_info()[1]
    return None


def _one_line(text: str) -> str:
    collapsed = _WHITESPACE_RE.sub(" ", text).strip()
    if len(collapsed) <= _MAX_DETAIL_CHARS:
        return collapsed
    return f"{collapsed[: _MAX_DETAIL_CHARS - 1]}…"


def _http_status(error: BaseException) -> int | None:
    response = getattr(error, "response", None)
    for candidate in (getattr(response, "status_code", None), getattr(error, "code", None)):
        if isinstance(candidate, int):
            return candidate
    return None


def _host(error: BaseException) -> str | None:
    request = getattr(error, "request", None)
    host = getattr(getattr(request, "url", None), "host", None)
    return host if isinstance(host, str) else None


def _error_kind(error: BaseException) -> str:
    name = type(error).__name__.lower()
    text = str(error).lower()
    if "timeout" in name or "timed out" in text:
        return "timeout"
    if _http_status(error) is not None:
        return "http"
    if "url" in name and "error" in name:
        return "network"
    if "service" in name or "capabilities" in text:
        return "service"
    return "error"


def _quiet_third_party_loggers() -> None:
    logging.getLogger(_OTLP_EXPORTER_LOGGER).setLevel(logging.CRITICAL)


def setup_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    _quiet_third_party_loggers()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            enrich_exceptions,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
