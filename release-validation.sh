#!/bin/bash

# Do not exit immediately on failure so we can always print the summary
set +e

FULL_STACK_VALIDATED=false
FALLBACK_ONLY=false
DOCKER_BUILD_VALIDATED=false
MIGRATIONS_VALIDATED=false
CRITICAL_JOURNEY_VALIDATED=false
VALIDATION_FAILED=false

if [ "$1" == "--fallback" ]; then
  echo "PARTIAL VALIDATION ONLY — NOT FULL MVP READY"
  echo "Running fallback local testing scripts to simulate the same tests if Docker isn't available..."
  FALLBACK_ONLY=true
  chmod +x release-test.sh
  if ./release-test.sh; then
    # We assume local tests pass critical journey logic if release-test.sh passes
    CRITICAL_JOURNEY_VALIDATED=true
  else
    VALIDATION_FAILED=true
  fi
else
  echo "Starting Release Validation (Strict Full-Stack Mode)..."
  echo "Attempting to run full Docker E2E stack validation..."

  # Ensure docker compose succeeds
  if docker compose build backend frontend; then
    DOCKER_BUILD_VALIDATED=true
  else
    echo "Docker build failed. Validation failed."
    VALIDATION_FAILED=true
  fi

  if [ "$VALIDATION_FAILED" = "false" ]; then
    if docker compose up -d postgres redis qdrant backend frontend; then
      echo "Docker stack started. Waiting for backend to become healthy..."

      # Wait for backend health to signify DB and cache are ready. Compose V2 handles basic dependencies but waiting for the HTTP port is safer.
      for i in {1..30}; do
        if docker compose exec -T backend curl -s http://127.0.0.1:8000/health > /dev/null || docker compose exec -T backend wget -q -O /dev/null http://127.0.0.1:8000/health; then
          echo "Backend is ready!"
          break
        fi
        sleep 2
        if [ "$i" -eq 30 ]; then
          echo "Backend did not become healthy in time."
          VALIDATION_FAILED=true
        fi
      done

      if [ "$VALIDATION_FAILED" = "false" ]; then
        # Run migrations FIRST
        if docker compose exec -T backend poetry run alembic upgrade head; then
            MIGRATIONS_VALIDATED=true
        else
            echo "Migrations failed in Docker stack."
            VALIDATION_FAILED=true
        fi

        # Run tests on the backend
        if [ "$VALIDATION_FAILED" = "false" ]; then
            if docker compose exec -T backend poetry run pytest -c pyproject.toml ../tests/; then
                CRITICAL_JOURNEY_VALIDATED=true
            else
                echo "Backend tests failed in Docker stack."
                VALIDATION_FAILED=true
                CRITICAL_JOURNEY_VALIDATED=false
            fi
        fi

        # Run frontend tests
        if [ "$VALIDATION_FAILED" = "false" ]; then
            if docker compose exec -T frontend npm run test; then
                :
            else
                echo "Frontend tests failed in Docker stack."
                VALIDATION_FAILED=true
                CRITICAL_JOURNEY_VALIDATED=false
            fi
        fi

        if [ "$VALIDATION_FAILED" = "false" ]; then
            FULL_STACK_VALIDATED=true
        fi
      fi
    else
      echo "Docker stack failed to start. Validation failed."
      VALIDATION_FAILED=true
    fi

    echo "Tearing down Docker stack..."
    docker compose down || true
  fi
fi

echo ""
echo "=== Validation Summary ==="
echo "FULL_STACK_VALIDATED=$FULL_STACK_VALIDATED"
echo "FALLBACK_ONLY=$FALLBACK_ONLY"
echo "DOCKER_BUILD_VALIDATED=$DOCKER_BUILD_VALIDATED"
echo "MIGRATIONS_VALIDATED=$MIGRATIONS_VALIDATED"
echo "CRITICAL_JOURNEY_VALIDATED=$CRITICAL_JOURNEY_VALIDATED"

if [ "$VALIDATION_FAILED" = "true" ]; then
    echo "Validation failed."
    exit 1
else
    if [ "$FALLBACK_ONLY" = "false" ]; then
        echo "Validation passed in strict mode."
    fi
fi
