from pathlib import Path
from uuid import uuid4

import pytest

from app.core.database import session_factory
from app.repositories.gameplay import GameUnitOfWork
from app.schemas.gameplay import CreateCharacterRequest
from app.services.gameplay import (
    CharacterNotFoundError,
    CharacterService,
    GameplayRuleViolation,
)


async def _created(player_id):
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        definitions = await service.creation_definitions()
        return await service.create_character(
            player_id,
            CreateCharacterRequest(
                name="Boundary Test",
                race_id=definitions.races[0].id,
                gender="Unspecified",
                alignment="NEUTRAL",
                starting_job_id=definitions.starting_jobs[0].id,
            ),
            "create-boundary",
        )


@pytest.mark.asyncio
async def test_cross_player_character_access_is_rejected(
    clean_gameplay_database: None,
) -> None:
    owner = uuid4()
    character = await _created(owner)

    async with session_factory() as session:
        with pytest.raises(CharacterNotFoundError):
            await CharacterService(GameUnitOfWork(session)).get_character(
                uuid4(), character.id
            )


@pytest.mark.asyncio
async def test_quest_item_cannot_be_dropped(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character = await _created(player_id)

    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        inventory = await service.inventory(player_id, character.id)
        seal = next(item for item in inventory.items if item.is_quest_item)
        with pytest.raises(GameplayRuleViolation, match="cannot be dropped"):
            await service.drop_item(
                player_id,
                character.id,
                seal.inventory_item_id,
                1,
                "drop-protected",
            )


@pytest.mark.asyncio
async def test_invalid_travel_does_not_change_location(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character = await _created(player_id)
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        locations = await service.locations(player_id, character.id)
        unreachable_id = next(
            location.id
            for location in locations
            if not location.reachable and location.id != character.current_location.id
        )
        with pytest.raises(GameplayRuleViolation):
            await service.travel(
                player_id, character.id, unreachable_id, "invalid-travel"
            )

    async with session_factory() as session:
        current = await CharacterService(GameUnitOfWork(session)).get_character(
            player_id, character.id
        )
    assert current.current_location.id == character.current_location.id


def test_gameplay_engines_have_no_ai_dependency() -> None:
    root = Path(__file__).parents[3] / "backend" / "app" / "engines"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))

    assert "app.ai" not in source
    assert "httpx" not in source
