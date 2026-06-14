import asyncio
from collections.abc import Awaitable, Callable
from typing import Literal

import asyncpg  # type: ignore[import-untyped]  # asyncpg does not publish typing metadata.
import httpx
import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import Settings, get_settings

HealthStatus = Literal["healthy", "degraded", "unhealthy"]
HealthCheck = Callable[[], Awaitable["DependencyHealth"]]


class DependencyHealth(BaseModel):
    """Public status for one infrastructure dependency."""

    status: HealthStatus


class SystemHealth(BaseModel):
    """Shallow health summary that does not expose dependency details."""

    status: HealthStatus
    services: dict[str, HealthStatus]


class HealthService:
    """Check foundation dependencies without reading or mutating game state."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def get_system_health(self) -> SystemHealth:
        """Return one readiness snapshot for all foundation dependencies."""
        checks: dict[str, HealthCheck] = {
            "database": self.get_database_health,
            "redis": self.get_redis_health,
            "qdrant": self.get_qdrant_health,
            "worker": self.get_worker_health,
            "ai_primary": self.get_ollama_health,
        }
        results = await asyncio.gather(*(check() for check in checks.values()))
        services = {
            name: result.status for name, result in zip(checks, results, strict=True)
        }
        services["ai_fallback"] = services["ai_primary"]
        overall: HealthStatus = (
            "healthy"
            if all(status == "healthy" for status in services.values())
            else "degraded"
        )
        return SystemHealth(status=overall, services=services)

    async def get_database_health(self) -> DependencyHealth:
        """Check PostgreSQL with a read-only connectivity query."""
        connection: asyncpg.Connection[asyncpg.Record] | None = None
        try:
            connection = await asyncpg.connect(self._settings.database_url, timeout=2)
            await connection.execute("SELECT 1")
        except (OSError, TimeoutError, asyncpg.PostgresError):
            return DependencyHealth(status="unhealthy")
        finally:
            if connection is not None:
                await connection.close()
        return DependencyHealth(status="healthy")

    async def get_redis_health(self) -> DependencyHealth:
        """Check Redis connectivity without storing application data."""
        client = redis.from_url(  # type: ignore[no-untyped-call]  # redis factory lacks metadata.
            self._settings.redis_url
        )
        try:
            await client.ping()
        except (OSError, TimeoutError, redis.RedisError):
            return DependencyHealth(status="unhealthy")
        finally:
            await client.aclose()
        return DependencyHealth(status="healthy")

    async def get_qdrant_health(self) -> DependencyHealth:
        """Check the Qdrant readiness endpoint without creating collections."""
        return await self._check_http_dependency(f"{self._settings.qdrant_url}/healthz")

    async def get_worker_health(self) -> DependencyHealth:
        """Check the RAG worker heartbeat without reading canonical state."""
        client = redis.from_url(  # type: ignore[no-untyped-call]
            self._settings.redis_url
        )
        try:
            heartbeat = await client.get("worker:rag:heartbeat")
        except (OSError, TimeoutError, redis.RedisError):
            return DependencyHealth(status="unhealthy")
        finally:
            await client.aclose()
        return DependencyHealth(
            status="healthy" if heartbeat == b"healthy" else "degraded"
        )

    async def get_ollama_health(self) -> DependencyHealth:
        """Check Ollama infrastructure without loading or invoking a model."""
        return await self._check_http_dependency(
            f"{self._settings.ollama_url}/api/tags"
        )

    async def _check_http_dependency(self, url: str) -> DependencyHealth:
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get(url)
                response.raise_for_status()
        except (httpx.HTTPError, OSError):
            return DependencyHealth(status="unhealthy")
        return DependencyHealth(status="healthy")
