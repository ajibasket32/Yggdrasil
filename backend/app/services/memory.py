import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from app.core.logging import get_logger
from app.core.metrics import (
    MEMORY_INDEX_JOBS_TOTAL,
    MEMORY_RECORDS_CREATED_TOTAL,
)
from app.models.memory import Memory, MemoryIndexJob
from app.rag.cache import MemoryContextCache
from app.rag.contracts import MemoryCreate, MemoryRecord
from app.rag.dispatch import IndexDispatcher
from app.rag.errors import IndexDispatchError, MemoryNotFoundError
from app.repositories.memory import MemoryUnitOfWork


class MemoryService:
    """Persist canonical memories before scheduling derived vector work."""

    def __init__(
        self,
        unit_of_work: MemoryUnitOfWork,
        dispatcher: IndexDispatcher,
        cache: MemoryContextCache,
        max_index_attempts: int,
    ) -> None:
        self._uow = unit_of_work
        self._dispatcher = dispatcher
        self._cache = cache
        self._max_index_attempts = max_index_attempts
        self._logger = get_logger()

    async def create_memory(
        self,
        player_id: UUID,
        candidate: MemoryCreate,
    ) -> MemoryRecord:
        """Create or return one canonical deduplicated memory."""
        content_hash = self.content_hash(candidate)
        lock_key = (
            f"memory:{player_id}:{candidate.memory_type.value}:"
            f"{candidate.entity_type}:{candidate.entity_id}:{content_hash}"
        )
        created = False
        async with self._uow:
            await self._uow.memories.lock_deduplication_key(lock_key)
            memory = await self._uow.memories.find_active_by_hash(
                player_id,
                candidate.memory_type.value,
                candidate.entity_type,
                candidate.entity_id,
                content_hash,
            )
            if memory is None:
                memory = Memory(
                    player_id=player_id,
                    memory_type=candidate.memory_type.value,
                    source_entity_type=candidate.source_entity_type,
                    source_entity_id=candidate.source_entity_id,
                    summary=candidate.summary,
                    importance=candidate.importance,
                    world_event_id=candidate.world_event_id,
                    entity_id=candidate.entity_id,
                    entity_type=candidate.entity_type,
                    participants=[
                        str(participant) for participant in sorted(candidate.participants, key=str)
                    ],
                    location_id=candidate.location_id,
                    tags=list(candidate.tags),
                    occurred_at=candidate.occurred_at,
                    content_hash=content_hash,
                    version=1,
                    status="ACTIVE",
                    index_status="PENDING",
                )
                await self._uow.memories.add(memory)
                created = True

        if created:
            MEMORY_RECORDS_CREATED_TOTAL.labels("created").inc()
            await self._create_job(memory.id, "UPSERT")
            await self._cache.invalidate_player(player_id)
        else:
            MEMORY_RECORDS_CREATED_TOTAL.labels("deduplicated").inc()
        return MemoryRecord.model_validate(memory)

    async def delete_memory(self, player_id: UUID, memory_id: UUID) -> None:
        """Soft-delete canonical memory before scheduling vector removal."""
        async with self._uow:
            memory = await self._uow.memories.get(
                player_id,
                memory_id,
                include_deleted=True,
                for_update=True,
            )
            if memory is None:
                raise MemoryNotFoundError("Memory was not found")
            if memory.deleted_at is not None:
                return
            self._uow.memories.mark_deleted(memory)

        await self._create_job(memory_id, "DELETE")
        await self._cache.invalidate_player(player_id)

    async def recover_unqueued_memories(self, limit: int = 100) -> list[UUID]:
        """Create missing durable jobs after broker or scheduling interruption."""
        jobs: list[MemoryIndexJob] = []
        async with self._uow:
            memories = await self._uow.memories.list_without_active_job(limit)
            for memory in memories:
                job = self._new_job(memory.id, "UPSERT")
                await self._uow.jobs.add(job)
                jobs.append(job)
        for job in jobs:
            await self._dispatch(job)
        return [job.id for job in jobs]

    async def _create_job(self, memory_id: UUID, operation: str) -> UUID:
        async with self._uow:
            job = self._new_job(memory_id, operation)
            await self._uow.jobs.add(job)
        await self._dispatch(job)
        return job.id

    def _new_job(self, memory_id: UUID, operation: str) -> MemoryIndexJob:
        return MemoryIndexJob(
            memory_id=memory_id,
            operation=operation,
            status="PENDING",
            attempts=0,
            max_attempts=self._max_index_attempts,
            next_attempt_at=datetime.now(UTC),
        )

    async def _dispatch(self, job: MemoryIndexJob) -> None:
        try:
            await self._dispatcher.enqueue(job.id)
        except IndexDispatchError:
            MEMORY_INDEX_JOBS_TOTAL.labels(job.operation.lower(), "dispatch_failed").inc()
            self._logger.warning(
                "Memory index job retained after dispatch failure",
                event_name="rag.index.dispatch_failed",
                category="RAG",
                job_id=str(job.id),
                operation=job.operation,
            )

    @staticmethod
    def content_hash(candidate: MemoryCreate) -> str:
        """Return a stable logical-memory deduplication hash."""
        payload = {
            "memory_type": candidate.memory_type.value,
            "source_entity_type": candidate.source_entity_type,
            "source_entity_id": str(candidate.source_entity_id),
            "entity_type": candidate.entity_type,
            "entity_id": str(candidate.entity_id),
            "summary": candidate.summary.casefold(),
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
