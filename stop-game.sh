#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "FAIL: Docker was not found on PATH."
  exit 1
fi

docker compose down
echo "Yggdrasil Chronicles has stopped."
