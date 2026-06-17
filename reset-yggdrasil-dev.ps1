# Requires PowerShell
$ErrorActionPreference = "Stop"

Write-Host "WARNING: This will destroy all local game data, saves, and databases." -ForegroundColor Red
$response = Read-Host "Are you sure you want to proceed? (y/N)"
if ($response -notmatch "^[yY]$") {
    Write-Host "Aborted." -ForegroundColor Yellow
    Return
}

Write-Host "Stopping services and removing volumes..." -ForegroundColor Cyan
docker compose down -v
Write-Host "Reset complete. You can now start fresh." -ForegroundColor Green
