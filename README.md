# astroimage

Self-hosted REST API and React SPA for spatial image processing (FITS, astroquery). This repository currently contains the **toolchain and project skeleton** — not product features.

See [AGENTS.md](./AGENTS.md) for the opinionated stack and feature-based architecture rules.

## Layout

```
astroimage/
  backend/       FastAPI (uv, src/ layout)
  frontend/      Vite + React 19 + TypeScript
  monitoring/    Prometheus, Grafana, Loki, Promtail, Tempo (external)
  docker-compose.yml
```

## Prerequisites

- Python 3.12+ (3.13 locally)
- [uv](https://docs.astral.sh/uv/)
- Node 22 + pnpm 11
- Docker (API distribution and local PostgreSQL)

## Backend

```bash
cd backend
uv sync --all-groups
cp ../.env.example ../.env
uv run uvicorn astroimage.main:app --reload --app-dir src
```

API docs: http://localhost:8000/docs  
Health: http://localhost:8000/health  
Metrics: http://localhost:8000/metrics  
OpenAPI: http://localhost:8000/openapi.json

```bash
uv run ruff check src tests
uv run ruff format src tests
uv run mypy
uv run lint-imports
uv run pytest
uv run python scripts/export_openapi.py
uv run alembic upgrade head
```

## Frontend

```bash
cd frontend
pnpm install
cp .env.example .env
pnpm generate:api   # requires backend/openapi.json
pnpm dev
```

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm build
```

Add shadcn components with `pnpm dlx shadcn@latest add <component>`.

## Docker

Application (API + PostgreSQL):

```bash
docker compose up --build
```

Observability (separate stack; scrapes `/metrics` and collects JSON logs):

```bash
docker compose -f monitoring/docker-compose.yml up
```

Set `OTLP_ENDPOINT=http://localhost:4318/v1/traces` on the API if Tempo is running.

## CI

GitHub Actions runs backend (uv + Ruff + mypy + import-linter + pytest) and frontend (Biome + tsc + Vitest + Playwright + build) in parallel.
