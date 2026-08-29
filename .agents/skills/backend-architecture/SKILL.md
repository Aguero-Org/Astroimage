---
name: backend-architecture
description: >-
  Feature-based FastAPI backend layout for astroimage. Use when adding or
  changing backend features, modules, tests, imports, architecture rules,
  shared infrastructure, or when unsure where a backend file belongs.
---

# Backend architecture (feature-based)

The backend package is `astroimage` under `backend/src/astroimage/`.

**Organize by feature/module, never by global technical layers.**

Do not reintroduce `api/`, `services/`, `domain/`, `infrastructure/`,
`models/`, `controllers/`, `daos/`, `schemas/`, or `repositories/` as
top-level packages under `astroimage/`.

## Comments policy (mandatory)

**Do not add explanatory comments** about:

- why a fix was made (Sonar, lint, review, bug workaround narrative);
- what code was added, removed, or changed;
- restating the obvious next line of code;
- changelog-style notes in source (`# fixed X`, `# no longer does Y`, `# required by Z tool`).

Prefer clear names, small functions, and tests over commentary.

Allowed only when strictly necessary:

- `# type: ignore[...]` / `# noqa: ...` with the required code, no essay;
- short non-obvious constraint that cannot be expressed in types or names
  (e.g. a protocol/interop quirk),
  never a history of the change.

Never leave dead commented-out code. Delete it.

## Canonical layout

```text
backend/src/astroimage/
├── <feature>/                 # e.g. health, payment
│   ├── controller.py          # HTTP endpoints (FastAPI router)
│   ├── schema.py              # Pydantic request/response DTOs
│   ├── service.py             # business orchestration
│   ├── dao.py                 # persistence access (or repository.py)
│   ├── model.py               # SQLAlchemy / persistence models
│   └── <subfeature>/          # only if the feature grows
├── shared/                    # cross-cutting infrastructure ONLY
│   ├── database.py
│   ├── deps.py
│   ├── logging.py
│   ├── metrics.py
│   ├── middleware.py
│   └── telemetry.py
├── config.py                  # settings (composition root)
└── main.py                    # app factory + router composition
```

### Naming

- Use Python-safe role modules: `controller.py`, not `user.controller.py`.
- The feature package already namespaces the role (`health.controller`).
- Prefer flat feature packages; add subpackages only when complexity requires it.

## Responsibilities and dependency direction

Inside a feature:

```text
controller → service → dao/repository → model
```

| Role | Responsibility | May depend on | Must not depend on |
|------|----------------|---------------|--------------------|
| `controller` | HTTP I/O, status codes | `service`, `schema`, `shared.deps` | `dao`, `model`, other features' internals |
| `service` | business logic | `dao`, `model`, `schema`, `shared` | `controller` |
| `dao` / `repository` | data access | `model`, `shared.database` | `service`, `controller` |
| `model` | persistence shape | SQLAlchemy / primitives | `service`, `controller`, `dao`, `schema` |
| `schema` | validation / DTOs | Pydantic only | `controller`, `service`, `dao`, `model` |

## Cross-cutting rules

- Features **may** use `astroimage.shared` and `astroimage.config`.
- `shared` must **never** import any feature.
- Features must **never** import `astroimage.main`.
- Compose feature routers in `main.py` (composition root), not in `shared`.
- Cross-feature imports are **forbidden by default**.
- If a legitimate cross-feature dependency is required:
  1. Prefer the other feature's **public `service`**.
  2. Never import another feature's `dao` or `model`.
  3. Document the pair in `ALLOWED_FEATURE_DEPENDENCIES` in
     `backend/tests/architecture/test_modules_architecture.py`.
  4. Add the new feature to import-linter contracts in `backend/pyproject.toml`.

## Adding a new feature

Example: `payment`.

1. Create the package and only the roles you need:

```text
backend/src/astroimage/payment/
├── __init__.py
├── controller.py
├── schema.py
├── service.py      # when needed
├── dao.py          # when needed
└── model.py        # when needed
```

2. Register the router in `main.build_api_router()`:

```python
from astroimage.payment.controller import router as payment_router
api_router.include_router(payment_router)
```

3. Add tests **only where they add value**:

```text
backend/tests/unit/payment/test_service.py
backend/tests/integration/payment/test_controller.py
backend/tests/architecture/payment/   # only for feature-specific arch rules
```

4. Update import-linter forbidden/source lists in `backend/pyproject.toml`
   for the new feature module (`astroimage.payment`).

5. pytestarch rules in `test_modules_architecture.py` auto-discover the
   new feature package — do not hardcode feature names there unless you
   are documenting an explicit exception.

6. Quality gates (from `backend/`):

```bash
uv run ruff format src tests
uv run ruff check src tests
uv run mypy
uv run lint-imports
uv run pytest
uv run python scripts/export_openapi.py   # if HTTP contract changed
```

If OpenAPI changed, regenerate the frontend client:

```bash
cd frontend && pnpm generate:api
```

## Tests layout (mirror of src)

```text
backend/tests/
├── architecture/
│   ├── test_modules_architecture.py   # global rules (pytestarch)
│   └── <feature>/                     # optional feature-specific rules
├── unit/
│   ├── <feature>/test_<component>.py
│   ├── shared/
│   └── config/                        # composition-root unit tests
└── integration/
    ├── <feature>/test_<component>.py
    ├── shared/
    └── test_openapi_contract.py       # cross-cutting contract suite
```

Mirror rule:

```text
src/astroimage/<module>/<component>.py
        ↓
tests/<unit|integration>/<module>/test_<component>.py
```

Rules:

- First level = test type (`architecture` | `unit` | `integration`).
- Second level = feature / `shared` / composition root (`config`).
- Do **not** create empty tests for symmetry.
- Do **not** use global component folders (`tests/unit/services/`, etc.).
- `shared` is infrastructure, not a business feature.

## What belongs in `shared`

Put code in `shared` only if it is truly cross-cutting infrastructure:

- database engine/session/`DeclarativeBase`
- logging, metrics, tracing
- HTTP middleware used by the whole app
- generic FastAPI dependencies (settings, DB session)

If it is domain-specific, keep it inside the feature even if two features
might eventually need something similar — extract later with a clear API.

## Out of scope (do not add without an explicit product decision)

- Authentication
- Rate limiting
- ARQ / Redis / Celery
- Extra caches beyond the stdlib
- MinIO / extra compose app services
- New HTTP clients, UI kits, or routers on the frontend side of the contract

## Stack reminders

- FastAPI, Pydantic v2, pydantic-settings
- SQLAlchemy 2.0 async + asyncpg; Alembic uses sync `psycopg`
- structlog JSON logs; Prometheus `/metrics`; OTLP traces
- uv + Ruff + mypy strict + import-linter + pytestarch
- OpenAPI is the only backend↔frontend contract (`backend/openapi.json`)

## Enforcement

| Mechanism | Location |
|-----------|----------|
| pytestarch feature/layer rules | `backend/tests/architecture/test_modules_architecture.py` |
| import-linter contracts | `backend/pyproject.toml` `[tool.importlinter.*]` |
| Project constraints | root `AGENTS.md` |

When architecture tests fail, **fix the code or document a real exception**.
Do not weaken rules just to get a green suite.
