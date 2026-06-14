from uuid import uuid4

import pytest
import redis.asyncio as redis

from app.ai.budget import RedisRequestBudget
from app.core.config import get_settings


@pytest.mark.asyncio
async def test_redis_budget_enforces_actor_limit() -> None:
    client = redis.from_url(get_settings().redis_url)
    actor_id = uuid4()
    budget = RedisRequestBudget(client, per_minute=2, per_hour=3)
    try:
        assert await budget.allow(actor_id) is True
        assert await budget.allow(actor_id) is True
        assert await budget.allow(actor_id) is False
    finally:
        await client.delete(
            f"ai-budget:minute:{actor_id}",
            f"ai-budget:hour:{actor_id}",
        )
        await client.aclose()
