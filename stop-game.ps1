$ErrorActionPreference = "Stop"

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

$DockerCommand = Get-DockerCommand
if ($null -eq $DockerCommand) {
    Write-Host "FAIL: Docker was not found on PATH." -ForegroundColor Red
    exit 1
}

Write-Host "Stopping Yggdrasil Chronicles..." -ForegroundColor Cyan
& $DockerCommand compose down
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: docker compose down failed." -ForegroundColor Red
    exit 1
}

Write-Host "Yggdrasil Chronicles has stopped." -ForegroundColor Green
