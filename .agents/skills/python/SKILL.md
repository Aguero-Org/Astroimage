---
name: python
description: >-
  Language-level Python for astroimage: typing, async, exceptions, logging,
  and uv. Use when editing Python that is not the feature layout. Service
  structure, HTTP, and tests stay in backend-architecture.
---

# Python (language)

The runtime image is Python 3.13 (`backend/Dockerfile`). `requires-python` stays `>=3.12`. Do not bump the image or the floor as a cleanup, and do not retune Ruff or mypy.

Feature layout, the HTTP session, the error body, and the test mirror live in `backend-architecture`. This skill does not own them.

## Types

- Annotate public functions and methods. Leave locals to inference. mypy strict is the gate.
- New generics use PEP 695: `def first[T](items: list[T]) -> T`, `class Box[T]`, `type Alias = int`. Do not rewrite an existing `TypeVar` unless that signature is already being edited.
- Prefer `X | None`, `Protocol` when only the methods matter, and `Literal` or `Enum` for a closed set.

## Errors

- Catch a specific exception. Chain with `raise NewError(...) from caught`.
- No bare `except`.
- `except Exception` belongs only at a process boundary that must roll back or translate and then re-raise or return the generic internal message (`shared/deps.py`, `shared/errors.py`). Do not copy it into a feature, and do not silence BLE001 with `# noqa`.

## Async

- Coroutines are for I/O. Do not call `time.sleep` or a blocking client (`requests`, sync database drivers) on the event loop.
- Astropy, NumPy, SciPy, and other CPU or file work goes through `asyncio.to_thread`.
- New fan-out that should fail together uses `asyncio.TaskGroup`. On `CancelledError`, clean up and re-raise.
- Do not replace `asyncio.gather(..., return_exceptions=True)` in the Gaia block query. That call keeps partial results on purpose; `TaskGroup` would cancel the other blocks.

## Libraries and logs

- Application logs go through `structlog.get_logger`. Do not add `print` or a new `logging.getLogger` for app logs. The stdlib logger that silences the OTLP exporter stays as it is.
- New filesystem paths use `pathlib`.
- Add dependencies with `uv add` and commit `uv.lock`. No library outside `AGENTS.md`.
- Never `eval` / `exec` / `pickle.loads` on untrusted bytes. `subprocess` takes an argument list, never `shell=True`. Tokens use `secrets`, not `random`.

## Values

- Request and response bodies stay Pydantic models in the feature `schema.py`.
- Rows stay SQLAlchemy models in `model.py`.
- A frozen dataclass is only for an in-memory value that is not an HTTP body and not a row.
