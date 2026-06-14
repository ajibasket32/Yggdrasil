from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.health import DependencyHealth, HealthService, SystemHealth

router = APIRouter(tags=["system"])
health_service = HealthService()


@router.get("/health/live", response_model=DependencyHealth)
async def get_liveness() -> DependencyHealth:
    """Return process liveness without contacting dependencies."""
    return DependencyHealth(status="healthy")


@router.get("/health", response_model=SystemHealth)
async def get_health() -> SystemHealth:
    """Return the shallow dependency readiness summary."""
    return await health_service.get_system_health()


@router.get("/health/db", response_model=DependencyHealth)
async def get_database_health() -> DependencyHealth:
    """Return PostgreSQL connectivity status."""
    return await health_service.get_database_health()


@router.get("/health/redis", response_model=DependencyHealth)
async def get_redis_health() -> DependencyHealth:
    """Return Redis connectivity status."""
    return await health_service.get_redis_health()


@router.get("/health/qdrant", response_model=DependencyHealth)
async def get_qdrant_health() -> DependencyHealth:
    """Return Qdrant connectivity status."""
    return await health_service.get_qdrant_health()


@router.get("/health/ai", response_model=DependencyHealth)
async def get_ai_health() -> DependencyHealth:
    """Return local Ollama infrastructure status without invoking a model."""
    return await health_service.get_ollama_health()


@router.get("/health/worker", response_model=DependencyHealth)
async def get_worker_health() -> DependencyHealth:
    """Return RAG worker heartbeat status."""
    return await health_service.get_worker_health()


@router.get("/metrics", include_in_schema=False)
async def get_metrics() -> Response:
    """Return Prometheus-compatible process metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
