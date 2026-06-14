from datetime import UTC, datetime, timedelta
from types import TracebackType
from uuid import UUID

from sqlalchemy import exists, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.models.memory import Memory, MemoryIndexJob


class MemoryRepository:
    """PostgreSQL access for canonical player-scoped memories."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock_deduplication_key(self, value: str) -> None:
        """Serialize concurrent creation of one logical memory."""
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:value, 0))"),
            {"value": value},
        )

    async def find_active_by_hash(
        self,
        player_id: UUID,
        memory_type: str,
        entity_type: str,
        entity_id: UUID,
        content_hash: str,
    ) -> Memory | None:
        result = await self._session.execute(
            select(Memory).where(
                Memory.player_id == player_id,
                Memory.memory_type == memory_type,
                Memory.entity_type == entity_type,
                Memory.entity_id == entity_id,
                Memory.content_hash == content_hash,
                Memory.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def add(self, memory: Memory) -> Memory:
        self._session.add(memory)
        await self._session.flush()
        return memory

    async def get(
        self,
        player_id: UUID,
        memory_id: UUID,
        *,
        include_deleted: bool = False,
        for_update: bool = False,
    ) -> Memory | None:
        statement = select(Memory).where(
            Memory.id == memory_id,
            Memory.player_id == player_id,
        )
        if not include_deleted:
            statement = statement.where(Memory.deleted_at.is_(None))
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        memory_id: UUID,
        *,
        for_update: bool = False,
    ) -> Memory | None:
        statement = select(Memory).where(Memory.id == memory_id)
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_by_ids(
        self,
        player_id: UUID,
        memory_ids: list[UUID],
    ) -> list[Memory]:
        if not memory_ids:
            return []
        result = await self._session.execute(
            select(Memory).where(
                Memory.player_id == player_id,
                Memory.id.in_(memory_ids),
                Memory.deleted_at.is_(None),
                Memory.status == "ACTIVE",
            )
        )
        return list(result.scalars().all())

    async def list_active(self, *, offset: int = 0, limit: int = 500) -> list[Memory]:
        result = await self._session.execute(
            select(Memory)
            .where(
                Memory.deleted_at.is_(None),
                Memory.status == "ACTIVE",
            )
            .order_by(Memory.created_at, Memory.id)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_without_active_job(self, limit: int = 100) -> list[Memory]:
        active_job = exists().where(
            MemoryIndexJob.memory_id == Memory.id,
            MemoryIndexJob.operation == "UPSERT",
            MemoryIndexJob.status.in_(("PENDING", "PROCESSING", "RETRY")),
        )
        result = await self._session.execute(
            select(Memory)
            .where(
                Memory.deleted_at.is_(None),
                Memory.index_status.in_(("PENDING", "FAILED")),
                ~active_job,
            )
            .order_by(Memory.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    @staticmethod
    def mark_deleted(memory: Memory) -> None:
        memory.status = "DELETED"
        memory.index_status = "DELETED"
        memory.deleted_at = datetime.now(UTC)


class MemoryIndexJobRepository:
    """PostgreSQL access for durable Qdrant synchronization jobs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, job: MemoryIndexJob) -> MemoryIndexJob:
        self._session.add(job)
        await self._session.flush()
        return job

    async def get_for_processing(self, job_id: UUID) -> MemoryIndexJob | None:
        result = await self._session.execute(
            select(MemoryIndexJob)
            .where(
                MemoryIndexJob.id == job_id,
                MemoryIndexJob.status.in_(("PENDING", "RETRY")),
                MemoryIndexJob.next_attempt_at <= datetime.now(UTC),
            )
            .with_for_update(skip_locked=True)
        )
        return result.scalar_one_or_none()

    async def get(
        self,
        job_id: UUID,
        *,
        for_update: bool = False,
    ) -> MemoryIndexJob | None:
        statement = select(MemoryIndexJob).where(MemoryIndexJob.id == job_id)
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_due_ids(self, limit: int = 100) -> list[UUID]:
        result = await self._session.execute(
            select(MemoryIndexJob.id)
            .where(
                MemoryIndexJob.status.in_(("PENDING", "RETRY")),
                MemoryIndexJob.next_attempt_at <= datetime.now(UTC),
            )
            .order_by(MemoryIndexJob.next_attempt_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def has_incomplete_jobs(self) -> bool:
        result = await self._session.execute(
            select(
                exists().where(
                    or_(
                        MemoryIndexJob.status.in_(("PENDING", "PROCESSING", "RETRY")),
                        MemoryIndexJob.status == "FAILED",
                    )
                )
            )
        )
        return bool(result.scalar_one())

    async def recover_stale_processing(self, stale_after_seconds: int) -> int:
        cutoff = datetime.now(UTC) - timedelta(seconds=stale_after_seconds)
        result = await self._session.execute(
            select(MemoryIndexJob)
            .where(
                MemoryIndexJob.status == "PROCESSING",
                MemoryIndexJob.updated_at < cutoff,
            )
            .with_for_update(skip_locked=True)
        )
        jobs = list(result.scalars().all())
        for job in jobs:
            job.status = "RETRY"
            job.next_attempt_at = datetime.now(UTC)
            job.last_error_code = "STALE_PROCESSING_LEASE"
        return len(jobs)


class MemoryUnitOfWork:
    """Own one transaction for memory and index-job repositories."""

    def __init__(self, session: AsyncSession) -> None:
        self.memories = MemoryRepository(session)
        self.jobs = MemoryIndexJobRepository(session)
        self._session = session
        self._transaction: AsyncSessionTransaction | None = None

    async def __aenter__(self) -> "MemoryUnitOfWork":
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._transaction is None:
            raise RuntimeError("MemoryUnitOfWork exited before it was entered")
        await self._transaction.__aexit__(exc_type, exc_value, traceback)
