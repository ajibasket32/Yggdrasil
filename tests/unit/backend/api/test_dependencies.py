from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import redis.asyncio as redis
from fastapi import Request
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_character_service,
    get_combat_service,
    get_narrative_service,
    get_save_service,
    get_world_service,
)
from app.core.config import Settings
from app.repositories.combat import CombatUnitOfWork
from app.repositories.gameplay import GameUnitOfWork
from app.repositories.narrative import NarrativeUnitOfWork
from app.repositories.save import SaveUnitOfWork
from app.repositories.world import WorldUnitOfWork
from app.services.combat import CombatService
from app.services.gameplay import CharacterService
from app.services.narrative import NarrativeService
from app.services.save import SaveService
from app.services.world import WorldService


def test_get_save_service_returns_configured_service() -> None:
    session = AsyncMock(spec=AsyncSession)

    service = get_save_service(session)

    assert isinstance(service, SaveService)
    assert isinstance(service._uow, SaveUnitOfWork)
    assert service._uow._session is session


def test_get_character_service_returns_configured_service() -> None:
    session = AsyncMock(spec=AsyncSession)

    service = get_character_service(session)

    assert isinstance(service, CharacterService)
    assert isinstance(service._uow, GameUnitOfWork)
    assert service._uow._session is session


def test_get_combat_service_returns_configured_service() -> None:
    session = AsyncMock(spec=AsyncSession)

    service = get_combat_service(session)

    assert isinstance(service, CombatService)
    assert isinstance(service._uow, CombatUnitOfWork)
    assert service._uow._session is session


def test_get_world_service_returns_configured_service() -> None:
    session = AsyncMock(spec=AsyncSession)

    service = get_world_service(session)

    assert isinstance(service, WorldService)
    assert isinstance(service._uow, WorldUnitOfWork)
    assert service._uow._session is session


@pytest.mark.asyncio
async def test_get_narrative_service_returns_configured_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock(spec=AsyncSession)

    request = MagicMock(spec=Request)
    request.app.state.http_client = AsyncMock(spec=httpx.AsyncClient)
    request.app.state.redis_client = AsyncMock(spec=redis.Redis)

    settings = Settings(
        database_url=SecretStr("postgresql+asyncpg://test:test@localhost:5432/test"),
        redis_url=SecretStr("redis://localhost:6379/0"),
        qdrant_url="http://localhost:6333",
        environment="test",
        openai_api_key=SecretStr("test-key"),
        cors_origins=["http://localhost"],
    )
    monkeypatch.setattr("app.api.dependencies.get_settings", lambda: settings)

    service = await get_narrative_service(request, session)

    assert isinstance(service, NarrativeService)
    assert isinstance(service._uow, NarrativeUnitOfWork)
    assert service._uow._session is session
