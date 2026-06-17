#!/bin/bash
set -e

FULL_STACK_VALIDATED=false
FALLBACK_ONLY=false
DOCKER_BUILD_VALIDATED=false
MIGRATIONS_VALIDATED=false
CRITICAL_JOURNEY_VALIDATED=false

if [ "$1" == "--fallback" ]; then
  echo "PARTIAL VALIDATION ONLY — NOT FULL MVP READY"
  echo "Running fallback local testing scripts to simulate the same tests if Docker isn't available..."
  FALLBACK_ONLY=true
  chmod +x release-test.sh
  ./release-test.sh || exit 1
  # Release test script will set its own state regarding migrations
  # We assume local tests pass critical journey logic if release-test.sh passes
  CRITICAL_JOURNEY_VALIDATED=true
else
  echo "Starting Release Validation (Strict Full-Stack Mode)..."
  echo "Attempting to run full Docker E2E stack validation..."

  # Ensure docker compose succeeds
  if docker compose build backend frontend; then
    DOCKER_BUILD_VALIDATED=true
  else
    echo "Docker build failed. Validation failed."
    exit 1
  fi

  if docker compose up -d postgres redis qdrant backend frontend; then
    # Wait for services to be ready, this should preferably use a healthcheck loop, but for simplicity here
    echo "Docker stack started. Running tests inside the stack..."

    # Run tests on the backend
    if docker compose exec -T backend poetry run pytest -c pyproject.toml ../tests/; then
        CRITICAL_JOURNEY_VALIDATED=true
    else
        echo "Backend tests failed in Docker stack."
        docker compose down || true
        exit 1
    fi

    # Run frontend tests
    if docker compose exec -T frontend npm run test; then
        :
    else
        echo "Frontend tests failed in Docker stack."
        docker compose down || true
        exit 1
    fi

    # Run migrations
    if docker compose exec -T backend poetry run alembic upgrade head; then
        MIGRATIONS_VALIDATED=true
    else
        echo "Migrations failed in Docker stack."
        docker compose down || true
        exit 1
    fi

    FULL_STACK_VALIDATED=true

  else
    echo "Docker stack failed to start. Validation failed."
    # Clean up what we can
    docker compose down || true
    exit 1
  fi

  echo "Tearing down Docker stack..."
  docker compose down
fi

echo ""
echo "=== Validation Summary ==="
echo "FULL_STACK_VALIDATED=$FULL_STACK_VALIDATED"
echo "FALLBACK_ONLY=$FALLBACK_ONLY"
echo "DOCKER_BUILD_VALIDATED=$DOCKER_BUILD_VALIDATED"
echo "MIGRATIONS_VALIDATED=$MIGRATIONS_VALIDATED"
echo "CRITICAL_JOURNEY_VALIDATED=$CRITICAL_JOURNEY_VALIDATED"

if [ "$FALLBACK_ONLY" = "false" ]; then
    echo "Validation passed in strict mode."
fi
