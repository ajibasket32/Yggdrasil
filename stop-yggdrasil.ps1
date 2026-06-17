# Requires PowerShell
$ErrorActionPreference = "Stop"

Write-Host "Stopping Yggdrasil Chronicles..." -ForegroundColor Cyan
docker compose down
Write-Host "Game stopped successfully." -ForegroundColor Green
