from typing import Any

import schemathesis

from astroimage.main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app)


@schema.parametrize()
def test_openapi_operations(case: schemathesis.Case[Any]) -> None:
    case.call_and_validate()
