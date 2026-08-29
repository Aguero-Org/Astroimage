<h1 style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; text-align: center;">
  <span>Astroimage</span>
  <img src="frontend/public/favicon.svg" width="128" height="128" alt="Astroimage logo">
</h1>

Self-hosted REST API and React SPA for spatial image processing (FITS, astroquery). This repository currently contains the **toolchain and project skeleton** — not product features.

See [AGENTS.md](./AGENTS.md) for the opinionated stack and feature-based architecture rules.

## Layout

```
astroimage/
  backend/       FastAPI (uv, src/ layout)
  frontend/      Vite + React 19 + TypeScript
  monitoring/    Prometheus, Grafana, Loki, Promtail, Tempo (external)
  sonar/         SonarQube Community (local quality analysis)
  docker-compose.yml
  sonar-project.properties
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
uv run astroimage serve --reload
```

API docs: http://localhost:8000/docs  
Health: http://localhost:8000/health  
Metrics: http://localhost:8000/metrics  
OpenAPI: http://localhost:8000/openapi.json

Project operations (`uv run astroimage …`):

```bash
uv run astroimage serve --reload
uv run astroimage openapi export
uv run astroimage db upgrade
uv run astroimage db revision -m "message" --autogenerate
```

Toolchain (`uv run <tool>`):

```bash
uv run ruff check src tests
uv run ruff format src tests
uv run mypy
uv run lint-imports
uv run pytest                  # also writes coverage.xml for Sonar
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
pnpm test:coverage            # lcov for SonarQube
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

## SonarQube (code quality)

Local server (separate stack):

```bash
docker compose -f sonar/docker-compose.yml up -d
```

UI: http://localhost:9000 — see [sonar/README.md](./sonar/README.md) for tokens, coverage, and scanner usage.

Root config: [`sonar-project.properties`](./sonar-project.properties) (backend Python + frontend TypeScript, coverage paths, exclusions for generated code).

## CI

GitHub Actions runs on pushes and pull requests to `main`, `develop`, and `feature/*`.

Backend: Ruff + mypy + import-linter + pytest + `astroimage openapi export` (drift check) + coverage.  
Frontend: Biome + tsc + Vitest coverage + Playwright + build (in parallel with backend).

When repository variable `SONAR_ENABLED=true` is set, a **SonarQube** job uploads analysis and enforces the Quality Gate:

| Name | Type | Purpose |
|------|------|--------|
| `SONAR_ENABLED` | variable | `true` to run the Sonar job |
| `SONAR_TOKEN` | secret | Analysis token (required when enabled) |
| `SONAR_HOST_URL` | variable | Self-hosted SonarQube URL (omit for SonarCloud) |
| `SONAR_ORGANIZATION` | variable | SonarCloud organization key (SonarCloud only) |
