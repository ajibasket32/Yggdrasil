from collections.abc import AsyncIterator
from typing import Annotated

import httpx
import redis.asyncio as redis
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import build_ai_orchestrator
from app.core.config import get_settings
from app.core.database import get_database_session
from app.rag.cache import MemoryContextCache
from app.rag.embedding import DeterministicTextEmbedder
from app.rag.qdrant import QdrantClient
from app.rag.retriever import MemoryRetriever
from app.repositories.combat import CombatUnitOfWork
from app.repositories.gameplay import GameStateRepository, GameUnitOfWork
from app.repositories.memory import MemoryRepository
from app.repositories.narrative import NarrativeUnitOfWork
from app.repositories.save import SaveUnitOfWork
from app.repositories.world import WorldUnitOfWork
from app.services.combat import CombatService
from app.services.gameplay import CharacterService
from app.services.narrative import NarrativeService
from app.services.narrative_context import NarrativeContextBuilder
from app.services.save import SaveService
from app.services.world import WorldService

DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


def get_save_service(session: DatabaseSession) -> SaveService:
    """Build a request-scoped save service without exposing SQL to routes."""
    return SaveService(SaveUnitOfWork(session), GameStateRepository(session))


SaveServiceDependency = Annotated[SaveService, Depends(get_save_service)]


def get_character_service(session: DatabaseSession) -> CharacterService:
    """Build a request-scoped gameplay service with one transaction boundary."""
    return CharacterService(GameUnitOfWork(session))


CharacterServiceDependency = Annotated[CharacterService, Depends(get_character_service)]


def get_combat_service(session: DatabaseSession) -> CombatService:
    """Build a request-scoped deterministic combat service."""
    return CombatService(CombatUnitOfWork(session))


CombatServiceDependency = Annotated[CombatService, Depends(get_combat_service)]


def get_world_service(session: DatabaseSession) -> WorldService:
    """Build a request-scoped deterministic world service."""
    return WorldService(WorldUnitOfWork(session))


WorldServiceDependency = Annotated[WorldService, Depends(get_world_service)]


async def get_narrative_service(
    request: Request,
    session: DatabaseSession,
) -> NarrativeService:
    """Compose request-scoped narrative, RAG, provider, and cache boundaries."""
    settings = get_settings()
    http_client: httpx.AsyncClient = request.app.state.http_client
    redis_client: redis.Redis = request.app.state.redis_client

    embedder = DeterministicTextEmbedder(settings.rag_embedding_dimensions)
    retriever = MemoryRetriever(
        MemoryRepository(session),
        embedder,
        QdrantClient(http_client, settings.qdrant_url, embedder.dimensions),
        MemoryContextCache(redis_client, settings.rag_cache_ttl_seconds),
    )
    unit_of_work = NarrativeUnitOfWork(session)
    return NarrativeService(
        unit_of_work,
        NarrativeContextBuilder(unit_of_work.narrative, retriever),
        build_ai_orchestrator(settings, http_client, redis_client),
    )


NarrativeServiceDependency = Annotated[NarrativeService, Depends(get_narrative_service)]
