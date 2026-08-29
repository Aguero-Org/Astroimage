$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$EnvFile = Join-Path $RepoRoot "sonar\.env"
if (-not (Test-Path $EnvFile)) {
    throw "Missing sonar/.env — create it with SONAR_TOKEN=..."
}

Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $name, $value = $_.Split("=", 2)
    Set-Item -Path "Env:$($name.Trim())" -Value $value.Trim()
}

if (-not $env:SONAR_TOKEN) {
    throw "SONAR_TOKEN is empty in sonar/.env"
}

$env:SONAR_HOST_URL = "http://host.docker.internal:9000"

Write-Host "==> Backend tests + coverage"
Push-Location (Join-Path $RepoRoot "backend")
uv run pytest -q
$cov = Get-Content "coverage.xml" -Raw
$cov = $cov -replace 'filename="src/', 'filename="backend/src/'
Set-Content -Path "coverage.xml" -Value $cov -NoNewline
Pop-Location

Write-Host "==> Frontend tests + coverage"
Push-Location (Join-Path $RepoRoot "frontend")
pnpm test:coverage
$lcovPath = "coverage\lcov.info"
if (Test-Path $lcovPath) {
    $lcov = Get-Content $lcovPath -Raw
    $lcov = $lcov -replace '\\', '/'
    $lcov = $lcov -replace 'SF:src/', 'SF:frontend/src/'
    Set-Content -Path $lcovPath -Value $lcov -NoNewline
}
Pop-Location

Write-Host "==> SonarScanner"
$mount = ($RepoRoot.Path -replace '\\', '/')
docker run --rm `
    -e SONAR_HOST_URL `
    -e SONAR_TOKEN `
    -v "${mount}:/usr/src" `
    -w /usr/src `
    sonarsource/sonar-scanner-cli:11

Write-Host ""
Write-Host "Dashboard: http://localhost:9000/dashboard?id=Astroimage"
