@echo off
setlocal

echo Checking Docker installation...
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker is not installed or not in your PATH.
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    goto :EOF
)

echo Checking if Docker is running...
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    goto :EOF
)

if not exist ".env" (
    echo First time setup: Creating .env file from .env.example...
    copy .env.example .env >nul
)

echo Starting Yggdrasil Chronicles...
docker compose up -d --build

if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to start the game.
    echo Common issues: Port conflicts, Docker Hub rate limits. Check WINDOWS_QUICKSTART.md.
    goto :EOF
)

echo.
echo =================================================
echo  Yggdrasil Chronicles is starting up!
echo  Please wait a minute for services to initialize.
echo  Game URL: http://localhost:8080
echo =================================================
echo.
