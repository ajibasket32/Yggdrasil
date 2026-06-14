import httpx
import redis.asyncio as redis

from app.ai.budget import RedisRequestBudget
from app.ai.orchestrator import AIOrchestrator
from app.ai.registry import build_provider_registry
from app.ai.validation import NarrativeValidator
from app.core.config import Settings


def build_ai_orchestrator(
    settings: Settings,
    http_client: httpx.AsyncClient,
    redis_client: redis.Redis,
) -> AIOrchestrator:
    """Compose the provider layer from caller-owned async clients."""
    registry = build_provider_registry(settings, http_client)
    budget = RedisRequestBudget(
        redis_client,
        per_minute=settings.ai_requests_per_minute,
        per_hour=settings.ai_requests_per_hour,
    )
    return AIOrchestrator(
        registry=registry,
        budget=budget,
        validator=NarrativeValidator(),
        attempts_per_provider=settings.ai_provider_attempts,
    )
