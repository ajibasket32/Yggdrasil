from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.core.database import session_factory
from app.main import app
from app.models.memory import Memory
from app.models.world import WorldEvent
from app.repositories.gameplay import GameStateRepository, GameUnitOfWork
from app.repositories.save import SaveUnitOfWork
from app.repositories.world import WorldUnitOfWork
from app.schemas.gameplay import CreateCharacterRequest
from app.services.gameplay import CharacterService
from app.services.save import SaveService
from app.services.world import WorldRuleViolation, WorldService


async def _character_at_greenwood(player_id: UUID):
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        definitions = await service.creation_definitions()
        warrior = next(
            value for value in definitions.starting_jobs if value.name == "Warrior"
        )
        character = await service.create_character(
            player_id,
            CreateCharacterRequest(
                name="World Tester",
                race_id=definitions.races[0].id,
                gender="Unspecified",
                alignment="NEUTRAL",
                starting_job_id=warrior.id,
            ),
            f"create-{player_id}",
        )
        locations = await service.locations(player_id, character.id)
        greenwood = next(
            value for value in locations if value.name == "Greenwood Verge"
        )
        await service.travel(
            player_id, character.id, greenwood.id, f"greenwood-{player_id}"
        )
    return character


@pytest.mark.asyncio
async def test_complete_world_flow_is_deterministic_and_persistent(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character = await _character_at_greenwood(player_id)

    async with session_factory() as session:
        world = WorldService(WorldUnitOfWork(session))
        quest = (await world.quests(player_id, character.id))[0]
        accepted = await world.accept_quest(
            player_id, character.id, quest.id, "accept-world-quest"
        )
        npc = (await world.npcs(player_id, character.id))[0]
        interaction = await world.interact(
            player_id, character.id, npc.id, "OFFER_HELP", "help-warden"
        )
        repeated = await world.interact(
            player_id, character.id, npc.id, "OFFER_HELP", "help-warden-again"
        )
    assert accepted.status == "ACTIVE"
    assert interaction.quest_progressed
    assert interaction.relationship.trust == 5
    assert not repeated.quest_progressed
    assert repeated.relationship.trust == 5

    async with session_factory() as session:
        save = await SaveService(
            SaveUnitOfWork(session), GameStateRepository(session)
        ).create_save(player_id, character.id, "Before hollow", "save-before-hollow")

    async with session_factory() as session:
        gameplay = CharacterService(GameUnitOfWork(session))
        locations = await gameplay.locations(player_id, character.id)
        crossroads = next(
            value for value in locations if value.name == "Ancient Crossroads"
        )
        await gameplay.travel(
            player_id, character.id, crossroads.id, "travel-crossroads"
        )

    async with session_factory() as session:
        world = WorldService(WorldUnitOfWork(session))
        dungeon = (await world.dungeons(player_id, character.id))[0]
        entered = await world.enter_dungeon(
            player_id, character.id, dungeon.id, "enter-hollow"
        )
        cleared = await world.clear_dungeon(
            player_id, character.id, dungeon.id, "clear-hollow"
        )
        completed = await world.submit_quest(
            player_id, character.id, quest.id, "submit-world-quest"
        )
        faction = (await world.factions(player_id, character.id))[0]
        joined = await world.join_faction(
            player_id, character.id, faction.id, "join-wardens"
        )
        journal = await world.journal(player_id, character.id)
    assert entered.entered
    assert cleared.cleared and not cleared.boss_alive
    assert completed.status == "COMPLETED" and completed.rewards_claimed
    assert joined.joined
    assert any(value.category == "QUEST_COMPLETED" for value in journal)

    async with session_factory() as session:
        await SaveService(
            SaveUnitOfWork(session), GameStateRepository(session)
        ).load_save(player_id, save.save_id, "load-before-hollow")

    async with session_factory() as session:
        world = WorldService(WorldUnitOfWork(session))
        persisted_quest = next(
            value
            for value in await world.quests(player_id, character.id)
            if value.id == quest.id
        )
        persisted_dungeon = next(
            value
            for value in await world.dungeons(player_id, character.id)
            if value.id == dungeon.id
        )
        persisted_faction = next(
            value
            for value in await world.factions(player_id, character.id)
            if value.id == faction.id
        )
        persisted_relationship = await world.relationship(
            player_id, character.id, npc.id
        )
    assert persisted_quest.status == "COMPLETED"
    assert persisted_dungeon.cleared and not persisted_dungeon.boss_alive
    assert persisted_faction.joined
    assert persisted_relationship.trust == 5

    async with session_factory() as session:
        memory_count = await session.scalar(select(func.count()).select_from(Memory))
        event_count = await session.scalar(select(func.count()).select_from(WorldEvent))
    assert memory_count == 4
    assert event_count == 3


@pytest.mark.asyncio
async def test_quest_failure_archive_and_invalid_transition_are_enforced(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character = await _character_at_greenwood(player_id)
    async with session_factory() as session:
        world = WorldService(WorldUnitOfWork(session))
        quest = (await world.quests(player_id, character.id))[0]
        await world.accept_quest(player_id, character.id, quest.id, "accept-fail")
        failed = await world.fail_quest(
            player_id, character.id, quest.id, "fail-active"
        )
        archived = await world.archive_quest(
            player_id, character.id, quest.id, "archive-failed"
        )
    assert failed.status == "FAILED"
    assert archived.status == "ARCHIVED"

    with pytest.raises(WorldRuleViolation, match="cannot transition"):
        async with session_factory() as session:
            await WorldService(WorldUnitOfWork(session)).accept_quest(
                player_id, character.id, quest.id, "accept-archived"
            )


@pytest.mark.asyncio
async def test_world_routes_enforce_player_ownership(
    clean_gameplay_database: None,
) -> None:
    owner_id = uuid4()
    other_id = uuid4()
    character = await _character_at_greenwood(owner_id)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/characters/{character.id}/quests",
            headers={"X-Player-ID": str(other_id)},
        )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "WORLD_ENTITY_NOT_FOUND"
