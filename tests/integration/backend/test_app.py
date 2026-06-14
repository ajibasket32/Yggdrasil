from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api import health
from app.core.health import DependencyHealth, SystemHealth
from app.main import app


def test_health_endpoint_returns_dependency_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response_health = SystemHealth(
        status="healthy",
        services={
            "database": "healthy",
            "redis": "healthy",
            "qdrant": "healthy",
            "worker": "healthy",
            "ai_primary": "healthy",
            "ai_fallback": "healthy",
        },
    )
    monkeypatch.setattr(
        health.health_service,
        "get_system_health",
        AsyncMock(return_value=response_health),
    )

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == response_health.model_dump()
    assert response.headers["X-Request-ID"]


@pytest.mark.parametrize(
    ("path", "method_name"),
    [
        ("/health/db", "get_database_health"),
        ("/health/redis", "get_redis_health"),
        ("/health/qdrant", "get_qdrant_health"),
        ("/health/ai", "get_ollama_health"),
    ],
)
def test_detailed_health_endpoint_returns_dependency_status(
    path: str,
    method_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        health.health_service,
        method_name,
        AsyncMock(return_value=DependencyHealth(status="healthy")),
    )

    with TestClient(app) as client:
        response = client.get(path)

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_worker_health_returns_heartbeat_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        health.health_service,
        "get_worker_health",
        AsyncMock(return_value=DependencyHealth(status="healthy")),
    )
    with TestClient(app) as client:
        response = client.get("/health/worker")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_metrics_endpoint_returns_prometheus_content() -> None:
    with TestClient(app) as client:
        response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
