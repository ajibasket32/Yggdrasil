import asyncio
from uuid import UUID

import httpx
import redis.asyncio as redis

from app.core.config import get_settings
from app.core.database import dispose_database, session_factory
from app.rag.cache import MemoryContextCache
from app.rag.celery_app import celery_app
from app.rag.dispatch import CeleryIndexDispatcher
from app.rag.embedding import DeterministicTextEmbedder
from app.rag.indexer import MemoryIndexer
from app.rag.qdrant import QdrantClient
from app.repositories.memory import MemoryUnitOfWork
from app.services.memory import MemoryService

settings = get_settings()


@celery_app.task(name="rag.process_memory_index_job")  # type: ignore[misc]
def process_memory_index_job(job_id: str) -> bool:
    """Run one durable index job in the Celery worker."""
    return asyncio.run(_process_memory_index_job(UUID(job_id)))


async def _process_memory_index_job(job_id: UUID) -> bool:
    try:
        async with (
            session_factory() as session,
            httpx.AsyncClient(timeout=settings.rag_qdrant_timeout_seconds) as client,
        ):
            indexer = MemoryIndexer(
                MemoryUnitOfWork(session),
                DeterministicTextEmbedder(settings.rag_embedding_dimensions),
                QdrantClient(
                    client,
                    settings.qdrant_url,
                    settings.rag_embedding_dimensions,
                ),
            )
            return await indexer.process(job_id)
    finally:
        await dispose_database()


@celery_app.task(name="rag.worker_heartbeat")  # type: ignore[misc]
def worker_heartbeat() -> None:
    """Publish a short-lived worker readiness heartbeat."""
    asyncio.run(_worker_heartbeat())


async def _worker_heartbeat() -> None:
    client = redis.from_url(settings.redis_url.get_secret_value())  # type: ignore[no-untyped-call]
    try:
        await client.set(
            "worker:rag:heartbeat",
            "healthy",
            ex=settings.worker_heartbeat_ttl_seconds,
        )
    finally:
        await client.aclose()


@celery_app.task(name="rag.recover_index_jobs")  # type: ignore[misc]
def recover_index_jobs() -> int:
    """Recover unannounced, stale, and due durable jobs."""
    return asyncio.run(_recover_index_jobs())


async def _recover_index_jobs() -> int:
    redis_client = redis.from_url(settings.redis_url.get_secret_value())  # type: ignore[no-untyped-call]
    dispatcher = CeleryIndexDispatcher(celery_app)
    try:
        async with session_factory() as session:
            unit_of_work = MemoryUnitOfWork(session)
            service = MemoryService(
                unit_of_work,
                dispatcher,
                MemoryContextCache(
                    redis_client,
                    settings.rag_cache_ttl_seconds,
                ),
                settings.rag_index_max_attempts,
            )
            recovered = await service.recover_unqueued_memories()
            async with unit_of_work:
                await unit_of_work.jobs.recover_stale_processing(300)
                due_ids = await unit_of_work.jobs.list_due_ids()
        for job_id in due_ids:
            await dispatcher.enqueue(job_id)
        return len(set(recovered + due_ids))
    finally:
        await redis_client.aclose()
        await dispose_database()
