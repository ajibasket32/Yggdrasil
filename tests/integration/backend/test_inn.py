import typing
from uuid import UUID, uuid4

import pytest

from app.core.database import session_factory
from app.repositories.gameplay import GameUnitOfWork
from app.repositories.world import WorldUnitOfWork
from app.schemas.gameplay import CreateCharacterRequest
from app.services.gameplay import CharacterService
from app.services.inn import InnService
from app.services.world import WorldRuleViolation


async def _create_test_character(player_id: UUID) -> typing.Any:
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        definitions = await service.creation_definitions()
        warrior = next(v for v in definitions.starting_jobs if v.name == "Warrior")
        character = await service.create_character(
            player_id,
            CreateCharacterRequest(
                name="Inn Tester",
                race_id=definitions.races[0].id,
                gender="Unspecified",
                alignment="NEUTRAL",
                starting_job_id=warrior.id,
            ),
            f"create-{player_id}",
        )
    return character


async def _travel_to_location(
    player_id: UUID, character_id: UUID, location_id: UUID
) -> None:
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        await service.travel(
            player_id,
            character_id,
            location_id,
            f"travel-{player_id}-{location_id}",
        )


async def _innkeeper_elena() -> typing.Any:
    async with session_factory() as session:
        elena = await WorldUnitOfWork(session).world.get_npc_by_name("Innkeeper Elena")
        assert elena is not None
        return elena


@pytest.mark.asyncio
async def test_inn_rest_success(clean_gameplay_database: None) -> None:
    player_id = uuid4()
    character = await _create_test_character(player_id)
    elena = await _innkeeper_elena()
    await _travel_to_location(player_id, character.id, elena.home_location_id)

    async with session_factory() as session:
        # Damage the character
        async with GameUnitOfWork(session) as uow:
            char = await uow.characters.get_owned(
                player_id, character.id, for_update=True
            )
            assert char is not None
            char.current_hp = 10
            char.current_mp = 0

        world_uow = WorldUnitOfWork(session)
        game_uow = GameUnitOfWork(session)
        inn_service = InnService(world_uow, game_uow)

        initial_gold = character.gold
        result = await inn_service.rest(player_id, character.id, elena.id, "rest-1")

        assert result.price_paid == InnService.INN_STAY_PRICE
        assert result.gold_remaining == initial_gold - InnService.INN_STAY_PRICE
        assert result.hp_restored > 0
        assert result.current_hp > 10


@pytest.mark.asyncio
async def test_inn_rest_insufficient_gold(clean_gameplay_database: None) -> None:
    player_id = uuid4()
    character = await _create_test_character(player_id)
    elena = await _innkeeper_elena()
    await _travel_to_location(player_id, character.id, elena.home_location_id)

    async with session_factory() as session:
        async with GameUnitOfWork(session) as uow:
            char = await uow.characters.get_owned(
                player_id, character.id, for_update=True
            )
            assert char is not None
            char.gold = 0

        world_uow = WorldUnitOfWork(session)
        game_uow = GameUnitOfWork(session)
        inn_service = InnService(world_uow, game_uow)

        with pytest.raises(WorldRuleViolation, match="Insufficient gold"):
            await inn_service.rest(player_id, character.id, elena.id, "rest-fail")
