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

1. Create project **Manually** with key `Astroimage` (matches `sonar-project.properties`; the key is case-sensitive).
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

The script runs backend + frontend tests with coverage, rewrites report
paths for the monorepo (`sonar/normalize-coverage.py`), and uploads the
analysis with `sonarsource/sonar-scanner-cli`.

Dashboard: http://localhost:9002/dashboard?id=Astroimage

> Project key is **case-sensitive** and must match the SonarQube project
> (`Astroimage` in `sonar-project.properties`).

## CI

The `sonar` job does not use SonarCloud or a GitHub secret. It starts
SonarQube Community in the runner (`sonar/ci-scan.sh`), creates the project
and analysis token against that container, scans, and uploads
`sonar/reports/issues.json` (agents) and `issues.md` (humans) as the
`sonar-report` artifact. The server is removed at the end of the job.

The job does not fail on the quality gate. A fresh server has no baseline,
so the new-code gate is not meaningful there. A scanner or compute-engine
failure still fails the job. Do not run `sonar/ci-scan.sh` locally: it
deletes its own Compose project volume.

## Quality profile and quality gate

Use the built-in **Sonar way** profile and the built-in **Sonar way**
quality gate. Do not copy the rule set into a custom profile. On a server
that splits the built-in profiles into Sonar way core, extended, and
comprehensive, keep **Sonar way core** as the baseline and extend it only
for a single justified rule.

The Sonar way gate applies to new code: no new issues, all new security
hotspots reviewed, coverage at least 80%, duplicated lines at most 3%.
It does not require cleaning historical code. `sonar.qualitygate.wait=true`
makes a local scanner wait for that gate. CI overrides it
(`-Dsonar.qualitygate.wait=false`) and uploads the report instead: the
server in that job has no previous analysis. New code detection on a
long-lived server needs full git history (`fetch-depth: 0` in the workflow).

Ruff, mypy, Biome, and `tsc` stay in CI. Do not import their reports
(`sonar.python.ruff.reportPaths`, `sonar.python.mypy.reportPaths`, or a
generic Biome import). Sonar cannot manage those rules in the profile, and
the same finding would fail both gates. The one local exception is
`css:S4662` on `frontend/src/index.css` (Tailwind at-rules).

Coverage reports are written from each workspace (`src/...`).
`sonar/normalize-coverage.py` rewrites them to `backend/src/...` and
`frontend/src/...` before the scan. CI runs that script after downloading
the coverage artifacts.
