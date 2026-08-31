from typing import Any

import pytest
import schemathesis

from astroimage.main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app)

_SKIP_PATHS = frozenset(
    {
        "/fits/metadata",
        "/image/{record_id}",
        "/image/{record_id}/histogram",
        "/image/{record_id}/info",
        "/image/{record_id}/sources",
        "/image",
        "/image/search",
    }
)


@schema.parametrize()
def test_openapi_operations(case: schemathesis.Case[Any]) -> None:
    if case.path in _SKIP_PATHS:
        pytest.skip(
            "paths requiring stored FITS records or external calls are covered by integration tests"
        )
    case.call_and_validate()
