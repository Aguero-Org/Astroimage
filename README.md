<p align="center">
  <img src="frontend/public/favicon.svg" width="128" height="128" alt="Logo de Astroimage">
</p>

<h1 align="center">Astroimage</h1>

## Elevator Pitch

La astronomía moderna genera una enorme cantidad de datos que están disponibles para cualquiera, pero acceder a ellos y, sobre todo, entenderlos, sigue siendo una barrera importante para quienes recién empiezan.

Para un estudiante o un astrónomo aficionado, encontrarse por primera vez con un archivo FITS, un catálogo con millones de objetos o distintas fuentes de datos astronómicos puede ser abrumador. No alcanza con tener acceso al dato: hay que entender qué contiene, cómo está estructurado, cómo visualizarlo y cómo relacionarlo con otras fuentes.

Astroimage nace para hacer ese proceso más accesible. La idea es construir una plataforma que permita explorar datos astronómicos de forma visual e intuitiva, empezando por un visor capaz de convertirse en una herramienta mucho más amplia.

A futuro, Astroimage busca conectar imágenes, catálogos y distintas fuentes astronómicas en un mismo entorno, reduciendo la distancia entre el dato científico y la persona que quiere aprender, investigar o simplemente explorar el universo.

En definitiva, queremos que trabajar con datos astronómicos deje de sentirse como entrar a un sistema diseñado exclusivamente para expertos y se convierta en una puerta de entrada para aprender astronomía haciendo.

## Introducción

Astroimage es una API REST autoalojada (FastAPI) y una SPA en React para procesar y analizar imágenes espaciales en FITS. Hoy ya no es un esqueleto: incluye búsqueda e ingestión vía astroquery/SkyView, persistencia en PostgreSQL y MinIO, render configurable, visor FITS interactivo con inspector, y detección de fuentes con photutils.

La pila y las reglas de arquitectura por feature están en [AGENTS.md](./AGENTS.md).

## Funcionalidades

- **SkyView y astroquery**: buscar e ingestir FITS por nombre de objeto o coordenadas (por ejemplo `M31`, `NGC 1300`).
- **Almacenamiento y persistencia**: cubo MinIO local para los FITS crudos y PostgreSQL (SQLAlchemy async + asyncpg) para los registros de metadatos.
- **Render de FITS**: pasar arrays FITS a imagen visual con stretch configurable (asinh, lineal, sqrt, log, etc.) y mapas de color.
- **Visor interactivo**: pan, zoom e inspección con OpenSeadragon, capas de marcadores y un inspector lateral (secciones Vista, Fuentes, Selección y Archivo).
- **Detección de fuentes**: fuentes puntuales y extendidas con `photutils` (DAOStarFinder / segmentación) y marcadores sobre la imagen.
- **Datos de prueba**: CLI para volcar y cargar snapshots (MinIO + PostgreSQL) hacia o desde GitHub Releases, y reconciliar registros con el object storage.

## Estructura

```
astroimage/
  backend/       FastAPI (uv, layout src/, features: fits, hub, render, sources, health)
  frontend/      Vite + React 19 + TypeScript + OpenSeadragon + TanStack Router/Query
  monitoring/    Prometheus, Grafana, Loki, Promtail, Tempo (observabilidad externa)
  sonar/         SonarQube Community (análisis de calidad local)
  docker-compose.yml (API + frontend + PostgreSQL + MinIO)
  sonar-project.properties
```

## Requisitos

- Python 3.12+ (3.13 en local)
- [uv](https://docs.astral.sh/uv/)
- Node 22 + pnpm 11
- Docker y Docker Compose (API, frontend, PostgreSQL 16 y MinIO)

## Backend

```bash
cd backend
uv sync --all-groups
cp ../.env.example ../.env
uv run astroimage serve --reload
```

Documentación de la API: http://localhost:8000/docs  
Salud: http://localhost:8000/health  
Métricas: http://localhost:8000/metrics  
OpenAPI: http://localhost:8000/openapi.json

### Operaciones del proyecto (`uv run astroimage …`)

```bash
# Servidor y contrato
uv run astroimage serve --reload
uv run astroimage openapi export

# Migraciones de base de datos
uv run astroimage db upgrade
uv run astroimage db revision -m "message" --autogenerate
uv run astroimage db reconcile

# Snapshots de datos de prueba (MinIO + PostgreSQL)
uv run astroimage seed dump -o seed.tar.gz
uv run astroimage seed load -f seed.tar.gz
uv run astroimage seed list -f seed.tar.gz
uv run astroimage seed delete -f seed.tar.gz
```

### Calidad y toolchain (`uv run <tool>`)

```bash
uv run ruff check src tests
uv run ruff format src tests
uv run mypy
uv run lint-imports
uv run pytest                  # escribe coverage.xml para Sonar
```

## Frontend

```bash
cd frontend
pnpm install
cp .env.example .env
pnpm generate:api   # cliente tipado a partir de backend/openapi.json
pnpm dev
```

Aplicación: http://localhost:5173

### Comandos del frontend

```bash
pnpm lint
pnpm format
pnpm typecheck
pnpm test
pnpm test:coverage            # lcov para SonarQube
pnpm test:e2e
pnpm build
pnpm generate:routes          # code-gen de TanStack Router
pnpm generate:api             # cliente Orval
```

Componentes shadcn: `pnpm dlx shadcn@latest add <component>`.

## Docker

Stack de la aplicación (API + frontend + PostgreSQL + MinIO):

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- PostgreSQL: `localhost:5432`
- API S3 de MinIO: http://localhost:9000
- Consola web de MinIO: http://localhost:9001 (`minioadmin` / `minioadmin`)

La SPA en el navegador sigue llamando a la API en `http://localhost:8000` (`VITE_API_BASE_URL`). No apuntes Vite a `http://api:8000`; ese hostname solo existe dentro de la red de Compose.

Observabilidad (stack aparte; scrapea `/metrics` y recoge logs JSON):

```bash
docker compose -f monitoring/docker-compose.yml up
```

Si Tempo está en marcha, configura `OTLP_ENDPOINT=http://localhost:4318/v1/traces` en la API.

## SonarQube (calidad de código)

Servidor local (stack aparte):

```bash
docker compose -f sonar/docker-compose.yml up -d
```

UI: http://localhost:9002 — ver [sonar/README.md](./sonar/README.md) para tokens, cobertura y el scanner.

Configuración raíz: [`sonar-project.properties`](./sonar-project.properties) (Python del backend + TypeScript del frontend, rutas de cobertura, exclusiones de código generado).

## CI

GitHub Actions corre en pushes y pull requests a `main`, `develop` y `feature/*`.

- **Backend**: Ruff + mypy + import-linter + pytest + `astroimage openapi export` (detección de drift) + cobertura.
- **Frontend**: Biome + tsc + cobertura Vitest + Playwright + build (en paralelo con el backend).

Si la variable de repositorio `SONAR_ENABLED=true` está activa, un job de **SonarQube** sube el análisis y exige el Quality Gate:

| Nombre | Tipo | Propósito |
|------|------|--------|
| `SONAR_ENABLED` | variable | `true` para ejecutar el job de Sonar |
| `SONAR_TOKEN` | secret | Token de análisis (obligatorio si está habilitado) |
| `SONAR_HOST_URL` | variable | URL de SonarQube autoalojado (omitir en SonarCloud) |
| `SONAR_ORGANIZATION` | variable | Clave de organización de SonarCloud (solo SonarCloud) |
