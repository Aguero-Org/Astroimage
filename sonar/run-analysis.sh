#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source sonar/.env

if [[ -z "${SONAR_TOKEN:-}" ]]; then
  echo "SONAR_TOKEN missing in sonar/.env" >&2
  exit 1
fi

export SONAR_HOST_URL="${SONAR_HOST_URL_SCANNER:-http://host.docker.internal:9002}"

echo "==> Backend tests + coverage"
(
  cd backend
  uv run pytest -q
)

echo "==> Frontend tests + coverage"
(
  cd frontend
  pnpm test:coverage
)

echo "==> Normalize coverage paths"
python3 sonar/normalize-coverage.py

echo "==> SonarScanner"
export MSYS_NO_PATHCONV=1
REPO="${ROOT}"
if command -v cygpath >/dev/null 2>&1; then
  REPO="$(cygpath -m "$ROOT")"
elif [[ -n "${WINDIR:-}" ]]; then
  REPO="$(cd "$ROOT" && pwd -W 2>/dev/null || echo "$ROOT")"
fi

docker run --rm \
  -e SONAR_HOST_URL \
  -e SONAR_TOKEN \
  -v "${REPO}:/usr/src" \
  -v /usr/src/backend/.cache \
  -w //usr/src \
  sonarsource/sonar-scanner-cli:11

echo
echo "Dashboard: http://localhost:9002/dashboard?id=Astroimage"
