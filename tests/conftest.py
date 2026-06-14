from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
import redis.asyncio as redis
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine
from app.rag.embedding import DeterministicTextEmbedder
from app.rag.qdrant import QdrantClient


@pytest_asyncio.fixture(autouse=True)
async def isolate_database_engine() -> AsyncIterator[None]:
    """Prevent pooled asyncpg connections from crossing pytest event loops."""
    await engine.dispose()
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def clean_save_database() -> AsyncIterator[None]:
    """Isolate persistence tests while retaining the migrated schema."""
    async with engine.begin() as connection:
        await connection.execute(
            text("TRUNCATE TABLE idempotency_records, save_games RESTART IDENTITY")
        )
    yield
    async with engine.begin() as connection:
        await connection.execute(
            text("TRUNCATE TABLE idempotency_records, save_games RESTART IDENTITY")
        )


@pytest_asyncio.fixture
async def clean_rag_infrastructure() -> AsyncIterator[None]:
    """Isolate canonical memories, vector collections, and RAG cache keys."""
    settings = get_settings()
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE TABLE memory_index_jobs, memory_links, memories "
                "RESTART IDENTITY CASCADE"
            )
        )
    redis_client = redis.from_url(
        settings.redis_url.get_secret_value()
    )  # type: ignore[no-untyped-call]
    async with httpx.AsyncClient(
        timeout=settings.rag_qdrant_timeout_seconds
    ) as http_client:
        qdrant = QdrantClient(
            http_client,
            settings.qdrant_url,
            DeterministicTextEmbedder().dimensions,
        )
        await qdrant.recreate_collections()
    keys = await redis_client.keys("rag-*")
    if keys:
        await redis_client.delete(*keys)
    yield
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE TABLE memory_index_jobs, memory_links, memories "
                "RESTART IDENTITY CASCADE"
            )
        )
    keys = await redis_client.keys("rag-*")
    if keys:
        await redis_client.delete(*keys)
    await redis_client.aclose()


@pytest_asyncio.fixture
async def clean_gameplay_database() -> AsyncIterator[None]:
    """Isolate player-owned game state while retaining seed definitions."""
    statement = text(
        "TRUNCATE TABLE "
        "narrative_records, memory_index_jobs, memory_links, memories, "
        "outbox_events, world_events, journal_entries, character_quests, "
        "relationships, character_dungeon_states, character_factions, "
        "combat_log_entries, combat_participants, "
        "combat_encounters, "
        "equipped_items, inventory_items, inventories, character_skills, "
        "character_jobs, character_location_discoveries, characters, "
        "idempotency_records, save_games RESTART IDENTITY CASCADE"
    )
    async with engine.begin() as connection:
        await connection.execute(statement)
    yield
    async with engine.begin() as connection:
        await connection.execute(statement)
