# Agent constraints for astroimage

This repository is opinionated. Do not introduce libraries, layers, or patterns outside this document. CI, linters, architecture tests, and pre-commit hooks must stay green.

## Layout

- `backend/` — FastAPI API (`src/` layout, package `astroimage`)
- `frontend/` — Vite + React SPA
- `monitoring/` — external observability compose (not part of the app image)
- Root `docker-compose.yml` — API + PostgreSQL only

## Allowed backend stack

- FastAPI, Pydantic v2, pydantic-settings
- uv, `pyproject.toml`, `uv.lock`
- Ruff (lint + format), mypy (strict)
- pytest, pytest-asyncio, httpx, pytest-cov, hypothesis, schemathesis
- import-linter + pytestarch
- structlog (JSON logs)
- prometheus-fastapi-instrumentator (`/metrics`)
- OpenTelemetry Python SDK (OTLP traces; Tempo is external)
- Uvicorn (dev), Gunicorn + Uvicorn workers (prod)
- SQLAlchemy 2.0 async + asyncpg + PostgreSQL + Alembic (sync driver `psycopg` for migrations)
- Scientific: Astropy, astroquery, NumPy, SciPy
- Docker multi-stage for the API

## Backend architecture (feature-based, enforced)

Organize `astroimage` by **feature/module**, not by global technical layers.

```text
src/astroimage/
├── health/                 # feature
│   ├── controller.py       # HTTP endpoints
│   ├── schema.py           # request/response DTOs
│   ├── service.py          # business orchestration (when needed)
│   ├── dao.py              # persistence access (when needed)
│   └── model.py            # ORM / persistence models (when needed)
├── shared/                 # cross-cutting infrastructure only
│   ├── database.py
│   ├── deps.py
│   ├── logging.py
│   ├── metrics.py
│   ├── middleware.py
│   └── telemetry.py
├── config.py               # settings (composition root)
└── main.py                 # app factory + router composition
```

### Responsibility rules

Intra-feature dependency direction:

`controller → service → dao/repository → model`

- `controller` — HTTP only; delegates to `service`; may use `schema`
- `service` — business logic; uses `dao` / `model` / `schema`
- `dao` / `repository` — data access only; uses `model`
- `model` — persistence representation; no service/controller/dao imports
- `schema` — Pydantic DTOs; no imports from controller/service/dao/model

### Cross-cutting rules

- Features may use `astroimage.shared` and `astroimage.config`
- `shared` must **not** import any feature
- Features must **not** import `main` (composition root imports features)
- Features must **not** depend on other features by default
- If a cross-feature dependency is required, prefer the other feature's **service**
  (public API), never its `dao` or `model`; document it in architecture tests
- Do **not** reintroduce global layer packages (`api/`, `services/`, `domain/`,
  `infrastructure/`, `models/`, `controllers/`, `daos/`, …)
- File names use Python-safe role modules (`controller.py`), not dotted names
  (`user.controller.py`)

Enforced by `tests/architecture/test_modules_architecture.py` (pytestarch) and
import-linter contracts in `backend/pyproject.toml`.

## Backend tests layout

```text
tests/
├── architecture/
│   ├── test_modules_architecture.py   # global feature-based rules
│   └── <feature>/                     # feature-specific arch rules (optional)
├── unit/
│   ├── <feature>/test_<component>.py
│   ├── shared/                        # shared infrastructure unit tests
│   └── config/                        # composition-root unit tests
└── integration/
    ├── <feature>/test_<component>.py
    ├── shared/
    └── test_openapi_contract.py       # cross-cutting contract suite
```

Mirror rule: `src/astroimage/<module>/<component>.py` →
`tests/<unit|integration>/<module>/test_<component>.py`.
Do not create empty test files for symmetry.

## Allowed frontend stack

- Vite + React 19 + TypeScript (`strict`)
- pnpm
- shadcn/ui + Tailwind CSS v4 + Radix primitives
- TanStack Query (server state only)
- Zustand (client/UI state only)
- TanStack Router
- native `fetch` via the Orval mutator in `src/lib/api-client.ts`
- Orval client generated from `backend/openapi.json`
- React Hook Form + Zod
- Biome (lint + format)
- Vitest + Testing Library + user-event + MSW
- Playwright

Do not mix TanStack Query with a global client store for server data.

## Out of current scope

- Authentication
- Rate limiting
- ARQ/Redis/Celery (defer until processing volume requires it)
- In-memory cache libraries beyond what Python already provides
- MinIO / extra compose services
- Storybook
- Kibana / Elasticsearch
- New UI kits, HTTP clients (axios, ky), or routers

## Contracts

- OpenAPI is the only API contract between backend and frontend
- After backend endpoint changes: export `backend/openapi.json` and run `pnpm generate:api` in frontend
- CORS is configured for the local Vite origin
- The API emits JSON logs and exposes `/metrics`; it does not ship Grafana/Prometheus/Loki/Tempo

## Quality gates

Every change must pass:

1. Backend: `ruff format`, `ruff check`, `mypy`, `lint-imports`, `pytest` (unit + integration + architecture)
2. Frontend: `biome check`, `tsc`, `vitest`, Playwright for critical flows
