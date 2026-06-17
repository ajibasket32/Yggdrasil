from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
import pytest
import redis.asyncio as redis
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import session_factory
from app.models.memory import Memory, MemoryIndexJob
from app.rag.cache import MemoryContextCache
from app.rag.contracts import MemoryCreate, MemoryType, RetrievalQuery
from app.rag.embedding import DeterministicTextEmbedder
from app.rag.indexer import MemoryIndexer
from app.rag.maintenance import MemoryMaintenanceService
from app.rag.qdrant import QdrantClient
from app.rag.retriever import MemoryRetriever
from app.repositories.memory import MemoryRepository, MemoryUnitOfWork
from app.services.memory import MemoryService


class RecordingDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[UUID] = []

    async def enqueue(self, job_id: UUID) -> None:
        self.job_ids.append(job_id)


def memory_candidate(
    entity_id: UUID,
    summary: str,
    *,
    tag: str = "bridge",
) -> MemoryCreate:
    return MemoryCreate(
        memory_type=MemoryType.LOCATION,
        source_entity_type="synthetic_event",
        source_entity_id=uuid4(),
        summary=summary,
        importance=6,
        entity_id=entity_id,
        entity_type="location",
        tags=(tag,),
        occurred_at=datetime.now(UTC),
    )


async def create_memory(
    player_id: UUID,
    candidate: MemoryCreate,
    dispatcher: RecordingDispatcher,
    redis_client: redis.Redis,
) -> UUID:
    settings = get_settings()
    async with session_factory() as session:
        service = MemoryService(
            MemoryUnitOfWork(session),
            dispatcher,
            MemoryContextCache(redis_client, settings.rag_cache_ttl_seconds),
            settings.rag_index_max_attempts,
        )
        return (await service.create_memory(player_id, candidate)).id


async def process_jobs(
    job_ids: list[UUID],
    http_client: httpx.AsyncClient,
) -> None:
    settings = get_settings()
    for job_id in job_ids:
        async with session_factory() as session:
            indexer = MemoryIndexer(
                MemoryUnitOfWork(session),
                DeterministicTextEmbedder(settings.rag_embedding_dimensions),
                QdrantClient(
                    http_client,
                    settings.qdrant_url,
                    settings.rag_embedding_dimensions,
                ),
            )
            assert await indexer.process(job_id) is True


@pytest.mark.asyncio
async def test_retrieval_enforces_scope_cache_and_deletion(
    clean_rag_infrastructure: None,
) -> None:
    settings = get_settings()
    player_id = uuid4()
    other_player_id = uuid4()
    allowed_entity = uuid4()
    blocked_entity = uuid4()
    dispatcher = RecordingDispatcher()
    redis_client = redis.from_url(settings.redis_url.get_secret_value())  # type: ignore[no-untyped-call]
    async with httpx.AsyncClient(
        timeout=settings.rag_qdrant_timeout_seconds
    ) as http_client:
        try:
            allowed_memory_id = await create_memory(
                player_id,
                memory_candidate(
                    allowed_entity,
                    "Ancient knights restored the northern bridge."
                    + " Reinforced stonework remains visible." * 20,
                ),
                dispatcher,
                redis_client,
            )
            await create_memory(
                player_id,
                memory_candidate(
                    blocked_entity,
                    "The southern orchard produced apples.",
                    tag="orchard",
                ),
                dispatcher,
                redis_client,
            )
            await create_memory(
                other_player_id,
                memory_candidate(
                    allowed_entity,
                    "Another player's bridge memory must remain private.",
                ),
                dispatcher,
                redis_client,
            )
            await process_jobs(dispatcher.job_ids, http_client)

            query = RetrievalQuery(
                player_id=player_id,
                query_text="Who restored the ancient bridge?",
                memory_types=(MemoryType.LOCATION,),
                allowed_entity_ids=frozenset({allowed_entity}),
                required_tags=frozenset({"bridge"}),
                as_of=datetime.now(UTC),
                limit=20,
                max_context_tokens=6000,
            )
            async with session_factory() as session:
                retriever = MemoryRetriever(
                    MemoryRepository(session),
                    DeterministicTextEmbedder(settings.rag_embedding_dimensions),
                    QdrantClient(
                        http_client,
                        settings.qdrant_url,
                        settings.rag_embedding_dimensions,
                    ),
                    MemoryContextCache(redis_client, settings.rag_cache_ttl_seconds),
                )
                first = await retriever.retrieve(query)
                second = await retriever.retrieve(query)
                bounded = await retriever.retrieve(
                    query.model_copy(update={"max_context_tokens": 100})
                )

            assert [item.memory_id for item in first.memories] == [allowed_memory_id]
            assert first.cache_hit is False
            assert second.cache_hit is True
            assert bounded.memories == ()
            assert bounded.truncated is True

            delete_dispatcher = RecordingDispatcher()
            async with session_factory() as session:
                service = MemoryService(
                    MemoryUnitOfWork(session),
                    delete_dispatcher,
                    MemoryContextCache(redis_client, settings.rag_cache_ttl_seconds),
                    settings.rag_index_max_attempts,
                )
                await service.delete_memory(player_id, allowed_memory_id)
            await process_jobs(delete_dispatcher.job_ids, http_client)

            async with session_factory() as session:
                after_delete = await MemoryRetriever(
                    MemoryRepository(session),
                    DeterministicTextEmbedder(settings.rag_embedding_dimensions),
                    QdrantClient(
                        http_client,
                        settings.qdrant_url,
                        settings.rag_embedding_dimensions,
                    ),
                    MemoryContextCache(redis_client, settings.rag_cache_ttl_seconds),
                ).retrieve(query)
            assert after_delete.memories == ()
        finally:
            await redis_client.aclose()


@pytest.mark.asyncio
async def test_qdrant_failure_is_retryable_and_canonical_memory_survives(
    clean_rag_infrastructure: None,
) -> None:
    settings = get_settings()
    player_id = uuid4()
    dispatcher = RecordingDispatcher()
    redis_client = redis.from_url(settings.redis_url.get_secret_value())  # type: ignore[no-untyped-call]
    try:
        memory_id = await create_memory(
            player_id,
            memory_candidate(uuid4(), "A retryable memory."),
            dispatcher,
            redis_client,
        )
        job_id = dispatcher.job_ids[0]

        async def unavailable(_: httpx.Request) -> httpx.Response:
            return httpx.Response(503)

        async with (
            httpx.AsyncClient(
                transport=httpx.MockTransport(unavailable)
            ) as failed_client,
            session_factory() as session,
        ):
            indexer = MemoryIndexer(
                MemoryUnitOfWork(session),
                DeterministicTextEmbedder(),
                QdrantClient(failed_client, "http://qdrant.invalid", 256),
            )
            assert await indexer.process(job_id) is False

        async with session_factory() as session:
            memory = await session.get(Memory, memory_id)
            job = await session.get(MemoryIndexJob, job_id)
            assert memory is not None
            assert memory.status == "ACTIVE"
            assert job is not None
            assert job.status == "RETRY"
            job.next_attempt_at = datetime.now(UTC)
            await session.commit()

        async with (
            httpx.AsyncClient(
                timeout=settings.rag_qdrant_timeout_seconds
            ) as recovered_client,
            session_factory() as session,
        ):
            recovered = MemoryIndexer(
                MemoryUnitOfWork(session),
                DeterministicTextEmbedder(),
                QdrantClient(
                    recovered_client,
                    settings.qdrant_url,
                    settings.rag_embedding_dimensions,
                ),
            )
            assert await recovered.process(job_id) is True
    finally:
        await redis_client.aclose()


@pytest.mark.asyncio
async def test_full_rebuild_queues_every_active_postgres_memory(
    clean_rag_infrastructure: None,
) -> None:
    settings = get_settings()
    player_id = uuid4()
    initial_dispatcher = RecordingDispatcher()
    redis_client = redis.from_url(settings.redis_url.get_secret_value())  # type: ignore[no-untyped-call]
    async with httpx.AsyncClient(
        timeout=settings.rag_qdrant_timeout_seconds
    ) as http_client:
        try:
            memory_ids = {
                await create_memory(
                    player_id,
                    memory_candidate(uuid4(), f"Rebuild memory {number}."),
                    initial_dispatcher,
                    redis_client,
                )
                for number in range(2)
            }
            await process_jobs(initial_dispatcher.job_ids, http_client)

            rebuild_dispatcher = RecordingDispatcher()
            async with session_factory() as session:
                maintenance = MemoryMaintenanceService(
                    MemoryUnitOfWork(session),
                    rebuild_dispatcher,
                    QdrantClient(
                        http_client,
                        settings.qdrant_url,
                        settings.rag_embedding_dimensions,
                    ),
                    settings.rag_index_max_attempts,
                )
                rebuild_jobs = await maintenance.rebuild()
            await process_jobs(rebuild_jobs, http_client)

            async with session_factory() as session:
                indexed = (
                    await session.scalars(
                        select(Memory).where(Memory.id.in_(memory_ids))
                    )
                ).all()
            assert len(rebuild_jobs) == 2
            assert {memory.index_status for memory in indexed} == {"INDEXED"}
        finally:
            await redis_client.aclose()
