#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "FAIL: Docker was not found on PATH."
  exit 1
fi

docker info >/dev/null

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Game URL:           http://localhost:8080"
echo "Backend health URL: http://localhost:8000/health"
echo "Logs command:       docker compose logs -f"
echo "Stop command:       ./stop-game.sh"
docker compose up --build
