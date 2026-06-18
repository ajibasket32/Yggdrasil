# Windows Quickstart Guide

**Version**: v1.0.0 (MVP Release) - 2026-06-18

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
   .\start-yggdrasil.ps1
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

### Accessing the Game
Once the script finishes starting the services, open your web browser and go to:
**http://localhost:8080**

## Common Issues

- **"Docker is not recognized..."**: Please ensure you have installed Docker Desktop and restarted your computer if necessary.
- **Port Conflicts (e.g., "port is already allocated")**: Ensure you do not have other services running on ports `8080`, `8000`, `3000`, `5432`, `6379`, or `6333`.
- **"Docker Hub rate limits" / "429 Too Many Requests"**: The game uses public mirrors by default, but if you still see this, try again later or log in to Docker Hub via Docker Desktop.
- **Failed health checks**: Sometimes components take a moment to start. If the game doesn't load immediately at `http://localhost:8080`, wait a minute and refresh the page.

## Stopping the Game

To stop the game services, run:
```powershell
.\stop-yggdrasil.ps1
```
