#!/usr/bin/env bash
set -euo pipefail

if [[ "${CI:-}" != "true" ]]; then
  echo "sonar/ci-scan.sh deletes its SonarQube volume. Refusing to run outside CI." >&2
  exit 1
fi

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

compose=(docker compose -p astroimage-sonar-ci -f sonar/docker-compose.yml -f sonar/docker-compose.ci.yml)
token_file="$(mktemp)"
chmod 600 "$token_file"

cleanup() {
  rm -f "$token_file"
  "${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

map_count="$(sysctl -n vm.max_map_count 2>/dev/null || echo 0)"
if [[ "$map_count" -lt 262144 ]]; then
  sudo sysctl -w vm.max_map_count=262144
fi

echo "==> Start ephemeral SonarQube Community"
"${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
"${compose[@]}" up -d --wait

echo "==> Create project and local analysis token"
python3 sonar/bootstrap_server.py --url http://127.0.0.1:9002 --token-file "$token_file"
SONAR_TOKEN="$(tr -d '\r\n' < "$token_file")"
if [[ -z "$SONAR_TOKEN" ]]; then
  echo "bootstrap did not write a token" >&2
  exit 1
fi
export SONAR_TOKEN
export SONAR_HOST_URL="http://sonarqube:9000"

echo "==> Scan"
docker run --rm --user 0 \
  --network astroimage-sonar-ci_default \
  -e SONAR_HOST_URL \
  -e SONAR_TOKEN \
  -v "${root}:/usr/src" \
  -w /usr/src \
  sonarsource/sonar-scanner-cli:11 \
  -Dsonar.working.directory=/usr/src/.scannerwork \
  -Dsonar.qualitygate.wait=false

if [[ -d .scannerwork ]]; then
  chmod -R a+rX .scannerwork
fi

echo "==> Export issues.json and issues.md"
python3 sonar/export_report.py \
  --url http://127.0.0.1:9002 \
  --token-file "$token_file" \
  --out sonar/reports \
  --report-task .scannerwork/report-task.txt
