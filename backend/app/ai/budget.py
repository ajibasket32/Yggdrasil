from time import time
from uuid import UUID

import redis.asyncio as redis

from app.ai.errors import BudgetUnavailableError


class RedisRequestBudget:
    """Redis-backed per-actor minute and hour request budget."""

    def __init__(
        self,
        client: redis.Redis,
        per_minute: int,
        per_hour: int,
    ) -> None:
        self._client = client
        self._per_minute = per_minute
        self._per_hour = per_hour

    async def allow(self, actor_id: UUID) -> bool:
        now = time()
        minute_key = f"ai-budget:minute:{actor_id}"
        hour_key = f"ai-budget:hour:{actor_id}"
        member = f"{now:.9f}"
        try:
            async with self._client.pipeline(transaction=True) as pipeline:
                pipeline.zremrangebyscore(minute_key, 0, now - 60)
                pipeline.zremrangebyscore(hour_key, 0, now - 3600)
                pipeline.zcard(minute_key)
                pipeline.zcard(hour_key)
                results = await pipeline.execute()
            minute_count = int(results[2])
            hour_count = int(results[3])
            if minute_count >= self._per_minute or hour_count >= self._per_hour:
                return False
            async with self._client.pipeline(transaction=True) as pipeline:
                pipeline.zadd(minute_key, {member: now})
                pipeline.zadd(hour_key, {member: now})
                pipeline.expire(minute_key, 61)
                pipeline.expire(hour_key, 3601)
                await pipeline.execute()
        except (OSError, TimeoutError, redis.RedisError) as error:
            raise BudgetUnavailableError("AI request budget is unavailable") from error
        return True
