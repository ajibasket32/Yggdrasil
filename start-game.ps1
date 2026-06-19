$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host "[Yggdrasil] $Message" -ForegroundColor Cyan
}

function Get-DockerCommand {
    $Docker = Get-Command "docker" -ErrorAction SilentlyContinue
    if ($Docker) {
        return $Docker.Source
    }

    $DefaultDockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    if (Test-Path -LiteralPath $DefaultDockerPath) {
        return $DefaultDockerPath
    }

    return $null
}

Write-Step "Checking Docker Desktop..."
$DockerCommand = Get-DockerCommand
if ($null -eq $DockerCommand) {
    Write-Host "FAIL: Docker was not found on PATH." -ForegroundColor Red
    Write-Host "Install Docker Desktop, start it, then open a new PowerShell window." -ForegroundColor Yellow
    exit 1
}

& $DockerCommand info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: Docker is installed but not running." -ForegroundColor Red
    Write-Host "Start Docker Desktop and wait until it says the engine is running." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path -LiteralPath ".env")) {
    Write-Step "Creating .env from .env.example..."
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
}

Write-Step "Starting the full game stack..."
Write-Host ""
Write-Host "Game URL:           http://localhost:8080" -ForegroundColor Green
Write-Host "Backend health URL: http://localhost:8000/health" -ForegroundColor Green
Write-Host "Logs command:       docker compose logs -f" -ForegroundColor White
Write-Host "Stop command:       .\stop-game.ps1" -ForegroundColor White
Write-Host ""

& $DockerCommand compose up --build
