$ErrorActionPreference = "Stop"

$RequiredFiles = @(
    "compose.yaml",
    ".env.example",
    "README.md",
    "WINDOWS_QUICKSTART.md",
    "frontend/package.json",
    "backend/pyproject.toml"
)

$Failed = $false

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

function Pass($Message) {
    Write-Host "PASS: $Message" -ForegroundColor Green
}

function Fail($Message) {
    Write-Host "FAIL: $Message" -ForegroundColor Red
    $script:Failed = $true
}

foreach ($File in $RequiredFiles) {
    if (Test-Path -LiteralPath $File) {
        Pass "$File exists"
    } else {
        Fail "$File is missing"
    }
}

$DockerCommand = Get-DockerCommand
if ($null -eq $DockerCommand) {
    Fail "Docker was not found on PATH"
} else {
    Pass "Docker command is available"
    & $DockerCommand compose config *> $null
    if ($LASTEXITCODE -eq 0) {
        Pass "docker compose config"
    } else {
        Fail "docker compose config"
    }
}

try {
    $Health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3
    if ($Health.StatusCode -ge 200 -and $Health.StatusCode -lt 500) {
        Pass "backend health endpoint responded"
    } else {
        Fail "backend health endpoint returned HTTP $($Health.StatusCode)"
    }
} catch {
    Write-Host "PARTIAL: backend health endpoint is not reachable. Start the game first with .\start-game.ps1." -ForegroundColor Yellow
}

try {
    $Frontend = Invoke-WebRequest -Uri "http://localhost:8080" -UseBasicParsing -TimeoutSec 3
    if ($Frontend.StatusCode -ge 200 -and $Frontend.StatusCode -lt 500) {
        Pass "game URL responded"
    } else {
        Fail "game URL returned HTTP $($Frontend.StatusCode)"
    }
} catch {
    Write-Host "PARTIAL: game URL is not reachable. Start the game first with .\start-game.ps1." -ForegroundColor Yellow
}

if ($Failed) {
    exit 1
}

Write-Host "Ready verification completed." -ForegroundColor Green
