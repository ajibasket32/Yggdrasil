import hashlib

import redis.asyncio as redis

from app.core.metrics import RAG_CACHE_OPERATIONS_TOTAL
from app.rag.contracts import MemoryContextPackage, RetrievalQuery


class MemoryContextCache:
    """Redis retrieval cache with per-player generation invalidation."""

    def __init__(self, client: redis.Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds

    async def get(self, query: RetrievalQuery) -> MemoryContextPackage | None:
        try:
            key = await self._key(query)
            payload = await self._client.get(key)
        except (OSError, TimeoutError, redis.RedisError):
            RAG_CACHE_OPERATIONS_TOTAL.labels("get", "error").inc()
            return None
        if payload is None:
            RAG_CACHE_OPERATIONS_TOTAL.labels("get", "miss").inc()
            return None
        RAG_CACHE_OPERATIONS_TOTAL.labels("get", "hit").inc()
        package = MemoryContextPackage.model_validate_json(payload)
        return package.model_copy(update={"cache_hit": True})

    async def set(
        self,
        query: RetrievalQuery,
        package: MemoryContextPackage,
    ) -> None:
        try:
            key = await self._key(query)
            await self._client.set(
                key,
                package.model_dump_json(),
                ex=self._ttl_seconds,
            )
        except (OSError, TimeoutError, redis.RedisError):
            RAG_CACHE_OPERATIONS_TOTAL.labels("set", "error").inc()
            return
        RAG_CACHE_OPERATIONS_TOTAL.labels("set", "success").inc()

    async def invalidate_player(self, player_id: object) -> None:
        try:
            await self._client.incr(f"rag-cache-version:{player_id}")
        except (OSError, TimeoutError, redis.RedisError):
            RAG_CACHE_OPERATIONS_TOTAL.labels("invalidate", "error").inc()
            return
        RAG_CACHE_OPERATIONS_TOTAL.labels("invalidate", "success").inc()

    async def _key(self, query: RetrievalQuery) -> str:
        version_value = await self._client.get(f"rag-cache-version:{query.player_id}")
        version = version_value.decode() if version_value else "0"
        digest = hashlib.sha256(query.model_dump_json().encode("utf-8")).hexdigest()
        return f"rag-context:{query.player_id}:{version}:{digest}"
