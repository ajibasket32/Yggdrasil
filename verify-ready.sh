#!/usr/bin/env bash
set -euo pipefail

required_files=(
  "compose.yaml"
  ".env.example"
  "README.md"
  "WINDOWS_QUICKSTART.md"
  "frontend/package.json"
  "backend/pyproject.toml"
)

for file in "${required_files[@]}"; do
  if [ -e "$file" ]; then
    echo "PASS: $file exists"
  else
    echo "FAIL: $file is missing"
    exit 1
  fi
done

if ! command -v docker >/dev/null 2>&1; then
  echo "FAIL: Docker was not found on PATH."
  exit 1
fi

docker compose config >/dev/null
echo "PASS: docker compose config"
echo "Ready verification completed."
