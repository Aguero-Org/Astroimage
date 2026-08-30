# SonarQube (local)

Self-hosted SonarQube for analyzing the monorepo. Separate from `docker-compose.yml` (app) and `monitoring/` (observability).

## Start the server

```bash
docker compose -f sonar/docker-compose.yml up -d
```

Open http://localhost:9002 — default credentials `admin` / `admin` (forced change on first login).
Host port **9002** avoids clashing with MinIO on **9000** (`docker-compose.yml`).

Wait until the container is healthy (`docker compose -f sonar/docker-compose.yml ps`).

## Create a project token

1. Create project **Manually** with key `astroimage` (matches `sonar-project.properties`).
2. Generate a **User token** (My Account → Security) or a project analysis token.
3. Export it:

```bash
# Windows PowerShell
$env:SONAR_TOKEN = "squ_..."
$env:SONAR_HOST_URL = "http://localhost:9002"

# bash
export SONAR_TOKEN=squ_...
export SONAR_HOST_URL=http://localhost:9002
```

## Produce coverage and scan (recommended)

Create `sonar/.env` (gitignored):

```env
SONAR_TOKEN=sqp_...
SONAR_HOST_URL=http://localhost:9002
```

From the repository root:

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File sonar/run-analysis.ps1
```

```bash
# Git Bash / Linux / macOS
bash sonar/run-analysis.sh
```

The script runs backend + frontend tests with coverage, fixes monorepo report
paths, and uploads the analysis with `sonarsource/sonar-scanner-cli`.

Dashboard: http://localhost:9002/dashboard?id=Astroimage

> Project key is **case-sensitive** and must match the SonarQube project
> (`Astroimage` in `sonar-project.properties`).

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
