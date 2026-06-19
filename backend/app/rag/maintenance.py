from contextlib import suppress
from datetime import UTC, datetime
from uuid import UUID

from app.models.memory import MemoryIndexJob
from app.rag.dispatch import IndexDispatcher
from app.rag.errors import IndexDispatchError
from app.rag.qdrant import QdrantClient
from app.repositories.memory import MemoryUnitOfWork


class MemoryMaintenanceService:
    """Rebuild Qdrant entirely from canonical PostgreSQL memories."""

    def __init__(
        self,
        unit_of_work: MemoryUnitOfWork,
        dispatcher: IndexDispatcher,
        qdrant: QdrantClient,
        max_index_attempts: int,
    ) -> None:
        self._uow = unit_of_work
        self._dispatcher = dispatcher
        self._qdrant = qdrant
        self._max_index_attempts = max_index_attempts

    async def rebuild(self) -> list[UUID]:
        """Recreate all collections and queue every active canonical memory."""
        await self._qdrant.recreate_collections()
        job_ids: list[UUID] = []
        offset = 0
        while True:
            async with self._uow:
                memories = await self._uow.memories.list_active(
                    offset=offset, limit=500
                )
                jobs = [
                    MemoryIndexJob(
                        memory_id=memory.id,
                        operation="UPSERT",
                        status="PENDING",
                        attempts=0,
                        max_attempts=self._max_index_attempts,
                        next_attempt_at=datetime.now(UTC),
                    )
                    for memory in memories
                ]
                for memory, job in zip(memories, jobs, strict=True):
                    memory.index_status = "PENDING"
                    await self._uow.jobs.add(job)
            for job in jobs:
                with suppress(IndexDispatchError):
                    await self._dispatcher.enqueue(job.id)
                job_ids.append(job.id)
            if len(memories) < 500:
                break
            offset += len(memories)
        return job_ids
