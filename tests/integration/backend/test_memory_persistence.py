from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import redis.asyncio as redis
import sqlalchemy as sa
from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.database import session_factory
from app.models.memory import Memory, MemoryIndexJob
from app.rag.cache import MemoryContextCache
from app.rag.contracts import MemoryCreate, MemoryType
from app.rag.errors import IndexDispatchError, MemoryNotFoundError
from app.repositories.memory import MemoryUnitOfWork
from app.services.memory import MemoryService


class CommitCheckingDispatcher:
    """Record jobs and prove canonical rows are visible before dispatch."""

    def __init__(self) -> None:
        self.job_ids: list[UUID] = []
        self.memory_visible_before_dispatch = False

    async def enqueue(self, job_id: UUID) -> None:
        async with session_factory() as verification_session:
            job = await verification_session.scalar(
                select(MemoryIndexJob).where(MemoryIndexJob.id == job_id)
            )
            memory = (
                await verification_session.get(Memory, job.memory_id) if job is not None else None
            )
        self.memory_visible_before_dispatch = memory is not None
        self.job_ids.append(job_id)


class FailingDispatcher:
    async def enqueue(self, job_id: UUID) -> None:
        raise IndexDispatchError(f"Broker unavailable for {job_id}")


def candidate(entity_id: UUID | None = None) -> MemoryCreate:
    target_id = entity_id or uuid4()
    return MemoryCreate(
        memory_type=MemoryType.WORLD,
        source_entity_type="world_event",
        source_entity_id=uuid4(),
        summary="The old northern bridge was restored.",
        importance=7,
        entity_id=target_id,
        entity_type="location",
        participants=frozenset({uuid4()}),
        tags=("Bridge", "Restored", "bridge"),
        occurred_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_memory_persists_before_dispatch_and_deduplicates(
    clean_rag_infrastructure: None,
) -> None:
    settings = get_settings()
    player_id = uuid4()
    dispatcher = CommitCheckingDispatcher()
    redis_client = redis.from_url(settings.redis_url.get_secret_value())  # type: ignore[no-untyped-call]
    try:
        async with session_factory() as session:
            service = MemoryService(
                MemoryUnitOfWork(session),
                dispatcher,
                MemoryContextCache(redis_client, 60),
                max_index_attempts=5,
            )
            memory = await service.create_memory(player_id, candidate())
            duplicate_candidate = candidate(memory.entity_id).model_dump()
            duplicate_candidate.update(
                {
                    "source_entity_id": memory.source_entity_id,
                    "summary": "  The old northern bridge was restored.  ",
                }
            )
            duplicate = await service.create_memory(
                player_id,
                MemoryCreate.model_validate(duplicate_candidate),
            )

        async with session_factory() as verification_session:
            memory_count = await verification_session.scalar(
                select(sa.func.count()).select_from(Memory)
            )
            job_count = await verification_session.scalar(
                select(sa.func.count()).select_from(MemoryIndexJob)
            )

        assert dispatcher.memory_visible_before_dispatch is True
        assert memory.id == duplicate.id
        assert memory_count == 1
        assert job_count == 1
        assert dispatcher.job_ids
    finally:
        await redis_client.aclose()


@pytest.mark.asyncio
async def test_dispatch_failure_retains_job_and_recovery_reannounces_it(
    clean_rag_infrastructure: None,
) -> None:
    settings = get_settings()
    player_id = uuid4()
    redis_client = redis.from_url(settings.redis_url.get_secret_value())  # type: ignore[no-untyped-call]
    try:
        async with session_factory() as session:
            service = MemoryService(
                MemoryUnitOfWork(session),
                FailingDispatcher(),
                MemoryContextCache(redis_client, 60),
                max_index_attempts=5,
            )
            memory = await service.create_memory(player_id, candidate())

        async with session_factory() as session:
            job = await session.scalar(
                select(MemoryIndexJob).where(MemoryIndexJob.memory_id == memory.id)
            )
            assert job is not None
            assert job.status == "PENDING"
            await session.execute(delete(MemoryIndexJob).where(MemoryIndexJob.id == job.id))
            await session.commit()

        recovery_dispatcher = CommitCheckingDispatcher()
        async with session_factory() as session:
            service = MemoryService(
                MemoryUnitOfWork(session),
                recovery_dispatcher,
                MemoryContextCache(redis_client, 60),
                max_index_attempts=5,
            )
            recovered = await service.recover_unqueued_memories()

        assert recovered == recovery_dispatcher.job_ids
        assert len(recovered) == 1
        assert recovery_dispatcher.memory_visible_before_dispatch is True
    finally:
        await redis_client.aclose()


@pytest.mark.asyncio
async def test_delete_is_idempotent_and_missing_memory_fails_closed(
    clean_rag_infrastructure: None,
) -> None:
    settings = get_settings()
    player_id = uuid4()
    dispatcher = CommitCheckingDispatcher()
    redis_client = redis.from_url(settings.redis_url.get_secret_value())  # type: ignore[no-untyped-call]
    try:
        async with session_factory() as session:
            service = MemoryService(
                MemoryUnitOfWork(session),
                dispatcher,
                MemoryContextCache(redis_client, 60),
                max_index_attempts=5,
            )
            memory = await service.create_memory(player_id, candidate())
            await service.delete_memory(player_id, memory.id)
            jobs_after_delete = len(dispatcher.job_ids)
            await service.delete_memory(player_id, memory.id)
            assert len(dispatcher.job_ids) == jobs_after_delete
            with pytest.raises(MemoryNotFoundError):
                await service.delete_memory(player_id, uuid4())
    finally:
        await redis_client.aclose()
