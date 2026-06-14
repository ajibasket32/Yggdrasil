from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import redis.asyncio as redis

from app.core.config import get_settings
from app.core.database import session_factory
from app.models.memory import MemoryIndexJob
from app.rag.cache import MemoryContextCache
from app.rag.contracts import (
    MemoryContextPackage,
    MemoryCreate,
    MemoryType,
    RetrievalQuery,
)
from app.repositories.memory import MemoryUnitOfWork
from app.services.memory import MemoryService


class RecordingDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[UUID] = []

    async def enqueue(self, job_id: UUID) -> None:
        self.job_ids.append(job_id)


@pytest.mark.asyncio
async def test_redis_failure_degrades_to_cache_miss() -> None:
    unavailable = redis.from_url(  # type: ignore[no-untyped-call]
        "redis://127.0.0.1:6399/0",
        socket_connect_timeout=0.05,
        socket_timeout=0.05,
    )
    query = RetrievalQuery(
        player_id=uuid4(),
        query_text="test",
        memory_types=(MemoryType.WORLD,),
        as_of=datetime.now(UTC),
    )
    cache = MemoryContextCache(unavailable, ttl_seconds=60)
    try:
        assert await cache.get(query) is None
        await cache.set(
            query,
            MemoryContextPackage(
                memories=(),
                estimated_tokens=0,
                truncated=False,
                cache_hit=False,
            ),
        )
        await cache.invalidate_player(query.player_id)
    finally:
        await unavailable.aclose()


@pytest.mark.asyncio
async def test_stale_worker_job_returns_to_retry_queue(
    clean_rag_infrastructure: None,
) -> None:
    settings = get_settings()
    dispatcher = RecordingDispatcher()
    redis_client = redis.from_url(settings.redis_url)  # type: ignore[no-untyped-call]
    try:
        async with session_factory() as session:
            service = MemoryService(
                MemoryUnitOfWork(session),
                dispatcher,
                MemoryContextCache(redis_client, 60),
                settings.rag_index_max_attempts,
            )
            await service.create_memory(
                uuid4(),
                MemoryCreate(
                    memory_type=MemoryType.WORLD,
                    source_entity_type="synthetic_event",
                    source_entity_id=uuid4(),
                    summary="A worker recovery memory.",
                    importance=5,
                    entity_id=uuid4(),
                    entity_type="world",
                    occurred_at=datetime.now(UTC),
                ),
            )

        async with session_factory() as session:
            job = await session.get(MemoryIndexJob, dispatcher.job_ids[0])
            assert job is not None
            job.status = "PROCESSING"
            await session.commit()

        async with session_factory() as session:
            unit_of_work = MemoryUnitOfWork(session)
            async with unit_of_work:
                recovered = await unit_of_work.jobs.recover_stale_processing(0)
            job = await session.get(MemoryIndexJob, dispatcher.job_ids[0])

        assert recovered == 1
        assert job is not None
        assert job.status == "RETRY"
        assert job.last_error_code == "STALE_PROCESSING_LEASE"
    finally:
        await redis_client.aclose()
