$ErrorActionPreference = "Stop"

if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "FAIL: Docker was not found on PATH." -ForegroundColor Red
    exit 1
}

Write-Host "Stopping Yggdrasil Chronicles..." -ForegroundColor Cyan
docker compose down
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: docker compose down failed." -ForegroundColor Red
    exit 1
}

Write-Host "Yggdrasil Chronicles has stopped." -ForegroundColor Green
