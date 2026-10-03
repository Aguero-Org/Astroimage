from __future__ import annotations

import pytest

from astroimage.shared.errors import (
    INTERNAL_ERROR_MESSAGE,
    AppError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    UnauthorizedError,
    UpstreamServiceError,
    as_app_error,
)

STATUS_CASES = [
    (BadRequestError, 400),
    (UnauthorizedError, 401),
    (ForbiddenError, 403),
    (NotFoundError, 404),
    (ConflictError, 409),
    (InternalServerError, 500),
    (UpstreamServiceError, 502),
]


@pytest.mark.parametrize(("error_type", "status_code"), STATUS_CASES)
def test_error_carries_status_code(error_type: type[AppError], status_code: int) -> None:
    assert error_type().status_code == status_code
    assert issubclass(error_type, AppError)


def test_message_defaults_when_not_provided() -> None:
    assert NotFoundError().message
    assert NotFoundError().message == NotFoundError.default_message


def test_explicit_message_wins() -> None:
    assert NotFoundError("no such record").message == "no such record"


def test_str_is_the_message() -> None:
    assert str(BadRequestError("bad input")) == "bad input"


@pytest.mark.parametrize(
    "error_type",
    [BadRequestError, UnauthorizedError, ForbiddenError, NotFoundError, ConflictError],
)
def test_client_errors_log_as_warning(error_type: type[AppError]) -> None:
    assert error_type().log_level == "warning"


@pytest.mark.parametrize("error_type", [InternalServerError, UpstreamServiceError])
def test_server_errors_log_as_error(error_type: type[AppError]) -> None:
    assert error_type().log_level == "error"


def test_app_error_passes_through() -> None:
    error = ConflictError("already exists")
    assert as_app_error(error) is error


def test_lookup_error_maps_to_not_found() -> None:
    mapped = as_app_error(KeyError("missing"))
    assert isinstance(mapped, NotFoundError)
    assert mapped.status_code == 404


def test_value_error_maps_to_bad_request() -> None:
    mapped = as_app_error(ValueError("invalid"))
    assert isinstance(mapped, BadRequestError)
    assert mapped.message == "invalid"


def test_os_error_maps_to_bad_request() -> None:
    mapped = as_app_error(OSError("cannot read"))
    assert isinstance(mapped, BadRequestError)
    assert mapped.message == "cannot read"


def test_unknown_error_maps_to_internal_without_leaking_message() -> None:
    mapped = as_app_error(RuntimeError("secret database url"))
    assert isinstance(mapped, InternalServerError)
    assert mapped.status_code == 500
    assert mapped.message == INTERNAL_ERROR_MESSAGE
    assert "secret database url" not in mapped.message


def test_base_app_error_is_internal_by_default() -> None:
    assert AppError().status_code == 500
    assert AppError().message == INTERNAL_ERROR_MESSAGE
