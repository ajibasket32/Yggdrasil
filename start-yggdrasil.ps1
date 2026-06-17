# Requires PowerShell
$ErrorActionPreference = "Stop"

Write-Host "Checking Docker installation..." -ForegroundColor Cyan
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker is not installed or not in your PATH." -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Return
}

Write-Host "Checking if Docker is running..." -ForegroundColor Cyan
try {
    $null = docker info 2>&1
} catch {
    Write-Host "ERROR: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    Return
}

if (-not (Test-Path ".env")) {
    Write-Host "First time setup: Creating .env file from .env.example..." -ForegroundColor Cyan
    Copy-Item ".env.example" -Destination ".env"
}

Write-Host "Starting Yggdrasil Chronicles..." -ForegroundColor Green
docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start the game." -ForegroundColor Red
    Write-Host "Common issues: Port conflicts, Docker Hub rate limits. Check WINDOWS_QUICKSTART.md." -ForegroundColor Yellow
    Return
}

Write-Host "`n=================================================" -ForegroundColor Green
Write-Host " Yggdrasil Chronicles is starting up!" -ForegroundColor Cyan
Write-Host " Please wait a minute for services to initialize." -ForegroundColor Yellow
Write-Host " Game URL: http://localhost:8080" -ForegroundColor White
Write-Host "=================================================`n" -ForegroundColor Green
