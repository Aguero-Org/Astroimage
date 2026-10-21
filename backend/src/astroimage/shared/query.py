from __future__ import annotations

from typing import Annotated

from fastapi import Query

HduIndex = Annotated[
    int | None,
    Query(ge=0, description="Optional image HDU index; defaults to the first 2D image HDU"),
]
