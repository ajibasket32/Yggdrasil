#!/bin/bash
set -e

SUITE=${1:-all}
SKIP_BUILD=false
KEEP_SERVICES=false
NO_SEED_CHECK=false

while [[ "$#" -gt 1 ]]; do
    case $1 in
        --skip-build) SKIP_BUILD=true ;;
        --keep-services) KEEP_SERVICES=true ;;
        --no-seed-check) NO_SEED_CHECK=true ;;
        *) SUITE=$1 ;;
    esac
    shift
done

COMPOSE_BASE="docker compose --env-file .env.test -f compose.test.yaml"

function cleanup {
    if [ "$KEEP_SERVICES" = false ]; then
        $COMPOSE_BASE down -v --remove-orphans
    fi
}
trap cleanup EXIT

if [ "$SKIP_BUILD" = true ]; then
    $COMPOSE_BASE up -d postgres redis qdrant
else
    $COMPOSE_BASE up -d --build postgres redis qdrant
    $COMPOSE_BASE build backend-test
fi

function run_test {
    $COMPOSE_BASE run --rm backend-test sh -lc "$1"
}

run_test "poetry run alembic -c alembic.ini upgrade head"

if [ "$NO_SEED_CHECK" = false ]; then
    run_test "python /tools/verify_test_seed_data.py || true"
fi

if [ "$SUITE" = "integration" ]; then
    run_test "poetry run pytest -c pyproject.toml ../tests/integration"
elif [ "$SUITE" = "regression" ]; then
    run_test "poetry run pytest -c pyproject.toml ../tests/regression"
else
    run_test "poetry run pytest -c pyproject.toml ../tests/integration ../tests/regression"
fi
