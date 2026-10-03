"""Global error translation.

Single place where an exception becomes an HTTP response: services and controllers
raise, ``register_exception_handlers`` decides the status code and the body.

Response bodies keep FastAPI's ``{"detail": ...}`` shape, so the existing client
contract and the 422 validation payload are untouched.
"""

from __future__ import annotations

import contextlib
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import Literal, cast

import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response

_log = structlog.get_logger("astroimage.errors")

INTERNAL_ERROR_MESSAGE = "Internal server error"

LogLevel = Literal["warning", "error"]
_LOGS: dict[LogLevel, Callable[..., None]] = {
    "warning": _log.warning,
    "error": _log.error,
}


class AppError(Exception):
    """Base class for errors that carry an HTTP meaning."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    default_message: str = INTERNAL_ERROR_MESSAGE
    log_level: LogLevel = "error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = HTTPStatus.BAD_REQUEST
    default_message = "Bad request"
    log_level = "warning"


class UnauthorizedError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    default_message = "Unauthorized"
    log_level = "warning"


class ForbiddenError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    default_message = "Forbidden"
    log_level = "warning"


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    default_message = "Not found"
    log_level = "warning"


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT
    default_message = "Conflict"
    log_level = "warning"


class InternalServerError(AppError):
    """Unexpected failure.

    Raise it with an already curated message; never with ``str(other_exception)``.
    Messages coming from unknown exceptions never reach the response (see
    ``as_app_error`` and ``internal_error_handler``).
    """

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_message = INTERNAL_ERROR_MESSAGE


class UpstreamServiceError(AppError):
    status_code = HTTPStatus.BAD_GATEWAY
    default_message = "Upstream service error"


_LEGACY_ERRORS: tuple[tuple[type[BaseException], type[AppError]], ...] = (
    (LookupError, NotFoundError),
    (ValueError, BadRequestError),
    (OSError, BadRequestError),
)


def as_app_error(exc: BaseException) -> AppError:
    """Map any exception to an :class:`AppError`, dropping unknown messages."""
    if isinstance(exc, AppError):
        return exc
    for exc_type, error_type in _LEGACY_ERRORS:
        if isinstance(exc, exc_type):
            return error_type(str(exc))
    return InternalServerError()


def _error_response(error: AppError, *, expose: bool = True) -> JSONResponse:
    detail = error.message if expose else INTERNAL_ERROR_MESSAGE
    return JSONResponse(status_code=error.status_code, content={"detail": detail})


def _log_safely(level: LogLevel, event: str, /, **kwargs: object) -> None:
    """Never let logging break the response.

    A logger that raises (unencodable stream, broken handler) would otherwise
    abort the handler and leave the client with an empty 500.
    """
    with contextlib.suppress(Exception):
        _LOGS[level](event, **kwargs)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    _log_safely(
        exc.log_level,
        "request_failed",
        status=exc.status_code,
        error_type=type(exc).__name__,
        method=request.method,
        path=request.url.path,
        detail=exc.message,
    )
    return _error_response(exc)


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    _log_safely(
        "error",
        "request_crashed",
        error_type=type(exc).__name__,
        method=request.method,
        path=request.url.path,
        exc_info=exc,
    )
    return _error_response(InternalServerError(), expose=False)


async def lookup_error_handler(request: Request, exc: LookupError) -> JSONResponse:
    return await app_error_handler(request, NotFoundError(str(exc)))


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return await app_error_handler(request, BadRequestError(str(exc)))


async def os_error_handler(request: Request, exc: OSError) -> JSONResponse:
    return await app_error_handler(request, BadRequestError(str(exc)))


def _register[E: Exception](
    app: FastAPI,
    exc_class: type[E],
    handler: Callable[[Request, E], Awaitable[Response]],
) -> None:
    """Register a narrowly typed handler under Starlette's wide signature.

    Starlette dispatches on the exception class, so widening here is safe and
    keeps each handler typed against the exception it actually receives.
    """

    async def wrapped(request: Request, exc: Exception) -> Response:
        return await handler(request, cast("E", exc))

    app.add_exception_handler(exc_class, wrapped)


def register_exception_handlers(app: FastAPI) -> None:
    """Install the global handlers; call once, before the app starts serving."""
    _register(app, AppError, app_error_handler)
    _register(app, LookupError, lookup_error_handler)
    _register(app, ValueError, value_error_handler)
    _register(app, OSError, os_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)
