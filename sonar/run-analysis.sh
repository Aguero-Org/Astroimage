#!/usr/bin/env bash
# Full monorepo SonarQube analysis (backend + frontend + coverage).
# Usage from repo root: bash sonar/run-analysis.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source sonar/.env

if [[ -z "${SONAR_TOKEN:-}" ]]; then
  echo "SONAR_TOKEN missing in sonar/.env" >&2
  exit 1
fi

# Scanner container reaches host-mapped Sonar port
export SONAR_HOST_URL="${SONAR_HOST_URL_SCANNER:-http://host.docker.internal:9000}"

echo "==> Backend tests + coverage"
(
  cd backend
  uv run pytest -q
  # Prefix paths so Sonar maps files under backend/src/...
  python -c "
from pathlib import Path
p = Path('coverage.xml')
p.write_text(p.read_text(encoding='utf-8').replace('filename=\"src/', 'filename=\"backend/src/'), encoding='utf-8')
"
)

echo "==> Frontend tests + coverage"
(
  cd frontend
  pnpm test:coverage
  python -c "
from pathlib import Path
p = Path('coverage/lcov.info')
text = p.read_text(encoding='utf-8').replace('\\\\', '/')
text = text.replace('SF:src/', 'SF:frontend/src/')
p.write_text(text, encoding='utf-8')
"
)

echo "==> SonarScanner"
export MSYS_NO_PATHCONV=1
REPO="${ROOT}"
# Git Bash on Windows: prefer Windows path for Docker Desktop mounts
if command -v cygpath >/dev/null 2>&1; then
  REPO="$(cygpath -m "$ROOT")"
elif [[ -n "${WINDIR:-}" ]]; then
  REPO="$(cd "$ROOT" && pwd -W 2>/dev/null || echo "$ROOT")"
fi

docker run --rm \
  -e SONAR_HOST_URL \
  -e SONAR_TOKEN \
  -v "${REPO}:/usr/src" \
  -w //usr/src \
  sonarsource/sonar-scanner-cli:11

echo
echo "Dashboard: http://localhost:9000/dashboard?id=Astroimage"
