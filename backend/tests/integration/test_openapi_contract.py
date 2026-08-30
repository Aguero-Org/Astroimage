from typing import Any

import pytest
import schemathesis

from astroimage.main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app)

_SKIP_PATHS = frozenset({"/fits/metadata", "/sources/detect", "/render/image"})


@schema.parametrize()
def test_openapi_operations(case: schemathesis.Case[Any]) -> None:
    if case.path in _SKIP_PATHS:
        pytest.skip("multipart file upload is covered by dedicated integration tests")
    case.call_and_validate()
