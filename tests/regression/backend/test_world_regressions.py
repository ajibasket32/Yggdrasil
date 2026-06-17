from uuid import UUID, uuid4

import pytest

from app.core.database import session_factory
from app.repositories.gameplay import GameStateRepository, GameUnitOfWork
from app.repositories.save import SaveUnitOfWork
from app.repositories.world import WorldUnitOfWork
from app.schemas.gameplay import CharacterSheet, CreateCharacterRequest
from app.services.gameplay import CharacterService
from app.services.save import SaveService
from app.services.world import WorldService


async def _ready_character(player_id: UUID) -> CharacterSheet:
    async with session_factory() as session:
        gameplay = CharacterService(GameUnitOfWork(session))
        definitions = await gameplay.creation_definitions()
        character = await gameplay.create_character(
            player_id,
            CreateCharacterRequest(
                name="Persistence Guard",
                race_id=definitions.races[0].id,
                gender="Unspecified",
                alignment="NEUTRAL",
                starting_job_id=definitions.starting_jobs[0].id,
            ),
            "create-persistence-guard",
        )
        greenwood = next(
            value
            for value in await gameplay.locations(player_id, character.id)
            if value.name == "Greenwood Verge"
        )
        await gameplay.travel(player_id, character.id, greenwood.id, "to-greenwood")
    return character


@pytest.mark.asyncio
async def test_old_save_cannot_resurrect_cleared_dungeon(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character = await _ready_character(player_id)
    async with session_factory() as session:
        save = await SaveService(SaveUnitOfWork(session), GameStateRepository(session)).create_save(
            player_id, character.id, "Before clear", "save-before-clear"
        )
    async with session_factory() as session:
        gameplay = CharacterService(GameUnitOfWork(session))
        crossroads = next(
            value
            for value in await gameplay.locations(player_id, character.id)
            if value.name == "Ancient Crossroads"
        )
        await gameplay.travel(player_id, character.id, crossroads.id, "to-crossroads")
    async with session_factory() as session:
        world = WorldService(WorldUnitOfWork(session))
        dungeon = (await world.dungeons(player_id, character.id))[0]
        await world.clear_dungeon(player_id, character.id, dungeon.id, "clear-once")
    async with session_factory() as session:
        await SaveService(SaveUnitOfWork(session), GameStateRepository(session)).load_save(
            player_id, save.save_id, "load-before-clear"
        )
    async with session_factory() as session:
        dungeon = next(
            value
            for value in await WorldService(WorldUnitOfWork(session)).dungeons(
                player_id, character.id
            )
            if value.id == dungeon.id
        )
    assert dungeon.cleared
    assert not dungeon.boss_alive
