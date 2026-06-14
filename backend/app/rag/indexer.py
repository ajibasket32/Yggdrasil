from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import UUID

from app.core.metrics import (
    CELERY_TASK_DURATION_SECONDS,
    CELERY_TASK_FAILURES_TOTAL,
    MEMORY_INDEX_JOBS_TOTAL,
)
from app.rag.embedding import DeterministicTextEmbedder
from app.rag.errors import QdrantError
from app.rag.qdrant import QdrantClient
from app.repositories.memory import MemoryUnitOfWork


class MemoryIndexer:
    """Synchronize durable memory jobs to the rebuildable Qdrant index."""

    def __init__(
        self,
        unit_of_work: MemoryUnitOfWork,
        embedder: DeterministicTextEmbedder,
        qdrant: QdrantClient,
    ) -> None:
        self._uow = unit_of_work
        self._embedder = embedder
        self._qdrant = qdrant

    async def process(self, job_id: UUID) -> bool:
        """Process one due job, retaining retry state on Qdrant failure."""
        started_at = perf_counter()
        async with self._uow:
            job = await self._uow.jobs.get_for_processing(job_id)
            if job is None:
                return False
            memory = await self._uow.memories.get_by_id(job.memory_id)
            if memory is None:
                job.status = "FAILED"
                job.last_error_code = "MEMORY_NOT_FOUND"
                return False
            job.status = "PROCESSING"
            job.attempts += 1
            operation = job.operation

        try:
            if operation == "UPSERT":
                await self._qdrant.upsert(
                    memory,
                    self._embedder.embed(memory.summary),
                )
            else:
                await self._qdrant.delete(memory)
        except QdrantError:
            await self._record_failure(job_id, "QDRANT_UNAVAILABLE")
            CELERY_TASK_FAILURES_TOTAL.labels(
                "memory_index",
                "qdrant_unavailable",
            ).inc()
            return False

        async with self._uow:
            current_job = await self._uow.jobs.get(job_id, for_update=True)
            current_memory = await self._uow.memories.get_by_id(
                memory.id, for_update=True
            )
            if current_job is None or current_memory is None:
                return False
            current_job.status = "COMPLETED"
            current_job.last_error_code = None
            if operation == "UPSERT" and current_memory.deleted_at is None:
                current_memory.index_status = "INDEXED"
            MEMORY_INDEX_JOBS_TOTAL.labels(operation.lower(), "completed").inc()
        CELERY_TASK_DURATION_SECONDS.labels("memory_index").observe(
            perf_counter() - started_at
        )
        return True

    async def _record_failure(self, job_id: UUID, error_code: str) -> None:
        async with self._uow:
            job = await self._uow.jobs.get(job_id, for_update=True)
            if job is None:
                return
            job.last_error_code = error_code
            if job.attempts >= job.max_attempts:
                job.status = "FAILED"
                memory = await self._uow.memories.get_by_id(
                    job.memory_id, for_update=True
                )
                if memory is not None and memory.deleted_at is None:
                    memory.index_status = "FAILED"
                MEMORY_INDEX_JOBS_TOTAL.labels(job.operation.lower(), "failed").inc()
            else:
                job.status = "RETRY"
                delay = min(300, 2**job.attempts)
                job.next_attempt_at = datetime.now(UTC) + timedelta(seconds=delay)
                MEMORY_INDEX_JOBS_TOTAL.labels(job.operation.lower(), "retry").inc()
