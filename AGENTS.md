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

## Backend layers (enforced)

`API → services → domain → infrastructure`

- `astroimage.api` — routers, HTTP deps, request middleware
- `astroimage.services` — application orchestration
- `astroimage.domain` — domain/scientific logic
- `astroimage.infrastructure` — DB, logging, metrics, tracing, external IO
- `astroimage.main` and `astroimage.config` are composition-root / settings, not layers

Lower layers must not import higher layers. No circular dependencies.

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
