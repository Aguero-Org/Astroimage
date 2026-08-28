# SonarQube (local)

Self-hosted SonarQube for analyzing the monorepo. Separate from `docker-compose.yml` (app) and `monitoring/` (observability).

## Start the server

```bash
docker compose -f sonar/docker-compose.yml up -d
```

Open http://localhost:9000 — default credentials `admin` / `admin` (forced change on first login).

Wait until the container is healthy (`docker compose -f sonar/docker-compose.yml ps`).

## Create a project token

1. Create project **Manually** with key `astroimage` (matches `sonar-project.properties`).
2. Generate a **User token** (My Account → Security) or a project analysis token.
3. Export it:

```bash
# Windows PowerShell
$env:SONAR_TOKEN = "squ_..."
$env:SONAR_HOST_URL = "http://localhost:9000"

# bash
export SONAR_TOKEN=squ_...
export SONAR_HOST_URL=http://localhost:9000
```

## Produce coverage, then scan

From the repository root:

```bash
# Backend coverage (writes backend/coverage.xml)
cd backend && uv run pytest && cd ..

# Frontend coverage (writes frontend/coverage/lcov.info)
cd frontend && pnpm test:coverage && cd ..

# Run the official scanner against the local server
docker run --rm \
  --network host \
  -e SONAR_HOST_URL="${SONAR_HOST_URL:-http://localhost:9000}" \
  -e SONAR_TOKEN="${SONAR_TOKEN}" \
  -v "${PWD}:/usr/src" \
  sonarsource/sonar-scanner-cli:11
```

On Docker Desktop (Windows/macOS), if `--network host` does not reach the host, use:

```bash
docker run --rm \
  -e SONAR_HOST_URL=http://host.docker.internal:9000 \
  -e SONAR_TOKEN="${SONAR_TOKEN}" \
  -v "${PWD}:/usr/src" \
  sonarsource/sonar-scanner-cli:11
```

## CI / SonarCloud

GitHub Actions job `sonar` runs when `SONAR_ENABLED=true`.

| Name | Type | Required | Notes |
|------|------|----------|--------|
| `SONAR_ENABLED` | variable | yes | set to `true` |
| `SONAR_TOKEN` | secret | yes | SonarQube or SonarCloud token |
| `SONAR_HOST_URL` | variable | SonarQube only | e.g. `https://sonar.example.com` |
| `SONAR_ORGANIZATION` | variable | SonarCloud only | organization key |

Project key defaults to `astroimage` (`sonar-project.properties`).

## Quality gate

The CI job waits for the Quality Gate and fails if status is not `OK`.
Adjust gate conditions in the SonarQube UI (Coverage, Duplications, Maintainability, Reliability, Security).
