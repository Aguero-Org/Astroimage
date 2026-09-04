<h1 style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; text-align: center;">
  <span>Astroimage</span>
  <img src="frontend/public/favicon.svg" width="128" height="128" alt="Astroimage logo">
</h1>

Self-hosted REST API and React SPA for spatial image processing and analysis (FITS, astroquery/SkyView, source detection with photutils, OpenSeadragon interactive viewer).

See [AGENTS.md](./AGENTS.md) for the opinionated stack and feature-based architecture rules.

## Features

- **SkyView & Astroquery Integration**: Search and ingest astronomical FITS files by target name/coordinates (e.g. `M31`, `NGC 1300`).
- **Object Storage & Persistence**: Local MinIO bucket for raw FITS assets and PostgreSQL (async via SQLAlchemy + asyncpg) for metadata records.
- **FITS Rendering**: Transform FITS arrays into visual formats with configurable stretching (Asinh, Linear, Sqrt, Log, etc.) and colormaps.
- **Interactive Deep Zoom Viewer**: Pan, zoom, and inspect astronomical images powered by OpenSeadragon and canvas overlays.
- **Source Detection**: Detect point and extended astronomical sources (stars, galaxies) using `photutils` (DAOStarFinder / segmentation) with interactive overlay markers.
- **Data Management & Seeds**: CLI tooling to dump/load test snapshots to GitHub releases and reconcile database records from object storage.

## Layout

```
astroimage/
  backend/       FastAPI (uv, src/ layout, features: fits, hub, render, sources, health)
  frontend/      Vite + React 19 + TypeScript + OpenSeadragon + TanStack Router/Query
  monitoring/    Prometheus, Grafana, Loki, Promtail, Tempo (external observability)
  sonar/         SonarQube Community (local quality analysis)
  docker-compose.yml (API + PostgreSQL + MinIO)
  sonar-project.properties
```

## Prerequisites

- Python 3.12+ (3.13 locally)
- [uv](https://docs.astral.sh/uv/)
- Node 22 + pnpm 11
- Docker & Docker Compose (API, PostgreSQL 16, and MinIO)

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

### Project operations (`uv run astroimage …`)

```bash
# Server & Contract
uv run astroimage serve --reload
uv run astroimage openapi export

# Database migrations
uv run astroimage db upgrade
uv run astroimage db revision -m "message" --autogenerate
uv run astroimage db reconcile

# Test dataset snapshots (MinIO + PostgreSQL)
uv run astroimage seed dump -o seed.tar.gz
uv run astroimage seed load -f seed.tar.gz
uv run astroimage seed list -f seed.tar.gz
uv run astroimage seed delete -f seed.tar.gz
```

### Quality & Toolchain (`uv run <tool>`)

```bash
uv run ruff check src tests
uv run ruff format src tests
uv run mypy
uv run lint-imports
uv run pytest                  # writes coverage.xml for Sonar
```

## Frontend

```bash
cd frontend
pnpm install
cp .env.example .env
pnpm generate:api   # generates typed client from backend/openapi.json
pnpm dev
```

App: http://localhost:5173

### Frontend commands

```bash
pnpm lint
pnpm format
pnpm typecheck
pnpm test
pnpm test:coverage            # lcov for SonarQube
pnpm test:e2e
pnpm build
pnpm generate:routes          # TanStack router code-gen
pnpm generate:api             # Orval API client code-gen
```

Add shadcn components with `pnpm dlx shadcn@latest add <component>`.

## Docker

Application stack (API + PostgreSQL + MinIO):

```bash
docker compose up --build
```

- API: http://localhost:8000
- PostgreSQL: `localhost:5432`
- MinIO S3 API: http://localhost:9000
- MinIO Web Console: http://localhost:9001 (`minioadmin` / `minioadmin`)

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

UI: http://localhost:9002 — see [sonar/README.md](./sonar/README.md) for tokens, coverage, and scanner usage.

Root config: [`sonar-project.properties`](./sonar-project.properties) (backend Python + frontend TypeScript, coverage paths, exclusions for generated code).

## CI

GitHub Actions runs on pushes and pull requests to `main`, `develop`, and `feature/*`.

- **Backend**: Ruff + mypy + import-linter + pytest + `astroimage openapi export` (drift check) + coverage.  
- **Frontend**: Biome + tsc + Vitest coverage + Playwright + build (in parallel with backend).

When repository variable `SONAR_ENABLED=true` is set, a **SonarQube** job uploads analysis and enforces the Quality Gate:

| Name | Type | Purpose |
|------|------|--------|
| `SONAR_ENABLED` | variable | `true` to run the Sonar job |
| `SONAR_TOKEN` | secret | Analysis token (required when enabled) |
| `SONAR_HOST_URL` | variable | Self-hosted SonarQube URL (omit for SonarCloud) |
| `SONAR_ORGANIZATION` | variable | SonarCloud organization key (SonarCloud only) |
