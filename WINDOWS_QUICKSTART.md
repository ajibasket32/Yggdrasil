# Windows Quickstart Guide

**Version**: v1.2.0-rc.1 (Ready-to-use hardening) - 2026-06-19

Welcome to Yggdrasil Chronicles! This guide will help you get the game running on your Windows machine easily.

## Prerequisites

1. **Docker Desktop**: The game requires Docker Desktop to run its services.
   - Download it from [Docker's official website](https://www.docker.com/products/docker-desktop).
   - Install and start Docker Desktop.

## Starting the Game

We've provided easy-to-use scripts to start the game.

1. **Open PowerShell or Command Prompt**.
2. **Navigate to the game directory**.
3. **Run the start script**:

   Using PowerShell:
   ```powershell
   .\start-game.ps1
   ```

   Using Command Prompt:
   ```cmd
   .\start-yggdrasil.cmd
   ```

### What the script does:
- Checks if Docker is installed and running.
- Creates a `.env` configuration file automatically if it's your first time.
- Downloads and starts all necessary game components.
- Tells you where to open the game in your browser!
- Shows the logs command and stop command.

### Accessing the Game
Once the script finishes starting the services, open your web browser and go to:
**http://localhost:8080**

Backend health is available at:
**http://localhost:8000/health**

To check whether the required files and Docker Compose setup are ready, run:

```powershell
.\verify-ready.ps1
```

## Common Issues

- **"Docker is not recognized..."**: Please ensure you have installed Docker Desktop and restarted your computer if necessary.
- **Port Conflicts (e.g., "port is already allocated")**: Ensure you do not have other services running on ports `8080`, `8000`, `3000`, `5432`, `6379`, or `6333`. If port `8080` is busy, edit `.env` and set `NGINX_PORT=8081`, then open `http://localhost:8081`.
- **"Docker Hub rate limits" / "429 Too Many Requests"**: The game uses public mirrors by default, but if you still see this, try again later or log in to Docker Hub via Docker Desktop.
- **Failed health checks**: Sometimes components take a moment to start. If the game doesn't load immediately at `http://localhost:8080`, wait a minute and refresh the page.
- **Docker is installed but not running**: Start Docker Desktop from the Start Menu and wait until it says the engine is running.
- **Need a clean database**: Stop the game, then run `docker compose down -v`. This deletes local development saves and starts fresh next time.
- **Need logs**: Run `docker compose logs -f` from the repository folder.

## Stopping the Game

To stop the game services, run:
```powershell
.\stop-game.ps1
```
