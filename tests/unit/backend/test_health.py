from unittest.mock import AsyncMock

import pytest

from app.core.health import DependencyHealth, HealthService


@pytest.mark.asyncio
async def test_system_health_when_all_dependencies_healthy_returns_healthy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HealthService()
    healthy_check = AsyncMock(return_value=DependencyHealth(status="healthy"))
    monkeypatch.setattr(service, "get_database_health", healthy_check)
    monkeypatch.setattr(service, "get_redis_health", healthy_check)
    monkeypatch.setattr(service, "get_qdrant_health", healthy_check)
    monkeypatch.setattr(service, "get_worker_health", healthy_check)
    monkeypatch.setattr(service, "get_ollama_health", healthy_check)

    result = await service.get_system_health()

    assert result.status == "healthy"
    assert set(result.services.values()) == {"healthy"}
    assert result.services["ai_fallback"] == "healthy"
