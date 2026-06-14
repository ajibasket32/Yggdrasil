from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.core.database import session_factory
from app.main import app
from app.models.combat import CombatLogEntry, GameOutboxEvent
from app.repositories.combat import CombatUnitOfWork
from app.repositories.gameplay import GameStateRepository, GameUnitOfWork
from app.repositories.save import SaveUnitOfWork
from app.schemas.combat import CombatActionRequest, StartCombatRequest
from app.schemas.gameplay import CreateCharacterRequest
from app.services.combat import CombatService
from app.services.gameplay import CharacterService
from app.services.save import SaveService


async def _create_at_encounter(player_id: UUID):
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        definitions = await service.creation_definitions()
        character = await service.create_character(
            player_id,
            CreateCharacterRequest(
                name="Combatant",
                race_id=definitions.races[0].id,
                gender="Unspecified",
                alignment="NEUTRAL",
                starting_job_id=definitions.starting_jobs[0].id,
            ),
            f"create-{player_id}",
        )
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        locations = await service.locations(player_id, character.id)
        destination = next(
            location
            for location in locations
            if location.reachable
            and location.id != character.current_location.id
            and location.name == "Greenwood Verge"
        )
        await service.travel(
            player_id, character.id, destination.id, f"travel-{player_id}"
        )
    return character


async def _win(player_id: UUID, character_id: UUID, seed: int = 17):
    async with session_factory() as session:
        service = CombatService(CombatUnitOfWork(session))
        encounter = (await service.available_encounters(player_id, character_id))[0]
        state = await service.start(
            player_id,
            StartCombatRequest(
                character_id=character_id,
                encounter_definition_id=encounter.id,
                seed=seed,
            ),
            f"start-{seed}",
        )
    action = 0
    while state.status == "ACTIVE":
        async with session_factory() as session:
            state = await CombatService(CombatUnitOfWork(session)).act(
                player_id,
                CombatActionRequest(
                    combat_id=state.combat_id,
                    action_type="ATTACK",
                ),
                f"attack-{seed}-{action}",
            )
        action += 1
        assert action < 20
    return state, action - 1


@pytest.mark.asyncio
async def test_victory_rewards_logs_events_and_save_restore_are_atomic(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    created = await _create_at_encounter(player_id)
    state, _ = await _win(player_id, created.id)

    assert state.status == "VICTORY"
    assert state.rewards.experience == 45
    assert state.rewards.gold == 18
    assert state.recent_log[-1].action_type == "VICTORY"

    async with session_factory() as session:
        sheet = await CharacterService(GameUnitOfWork(session)).get_character(
            player_id, created.id
        )
        log_count = await session.scalar(
            select(func.count())
            .select_from(CombatLogEntry)
            .where(CombatLogEntry.encounter_id == state.combat_id)
        )
        event_count = await session.scalar(
            select(func.count())
            .select_from(GameOutboxEvent)
            .where(GameOutboxEvent.aggregate_id == state.combat_id)
        )
    assert sheet.experience == 45
    assert sheet.gold == created.gold + 18
    assert int(log_count or 0) >= 3
    assert int(event_count or 0) >= 3

    async with session_factory() as session:
        save = await SaveService(
            SaveUnitOfWork(session), GameStateRepository(session)
        ).create_save(player_id, created.id, "After combat", "save-combat-result")
    async with session_factory() as session:
        await CharacterService(GameUnitOfWork(session)).award_experience(
            player_id, created.id, 60, "mutate-after-combat-save"
        )
    async with session_factory() as session:
        loaded = await SaveService(
            SaveUnitOfWork(session), GameStateRepository(session)
        ).load_save(player_id, save.save_id, "restore-combat-result")
    assert loaded.snapshot.character["experience"] == 45


@pytest.mark.asyncio
async def test_combat_action_idempotency_does_not_duplicate_rewards(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    created = await _create_at_encounter(player_id)
    state, final_action = await _win(player_id, created.id, seed=23)

    async with session_factory() as session:
        replayed = await CombatService(CombatUnitOfWork(session)).act(
            player_id,
            CombatActionRequest(
                combat_id=state.combat_id,
                action_type="ATTACK",
            ),
            f"attack-23-{final_action}",
        )
    assert replayed == state

    async with session_factory() as session:
        sheet = await CharacterService(GameUnitOfWork(session)).get_character(
            player_id, created.id
        )
    assert sheet.gold == created.gold + 18
    assert sheet.experience == 45


@pytest.mark.asyncio
async def test_combat_http_flow_exposes_replayable_log(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    created = await _create_at_encounter(player_id)
    headers = {"X-Player-ID": str(player_id)}
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        encounters = await client.get(
            f"/api/v1/characters/{created.id}/encounters", headers=headers
        )
        start = await client.post(
            "/api/v1/combat/start",
            headers={**headers, "Idempotency-Key": "http-start-combat"},
            json={
                "character_id": str(created.id),
                "encounter_definition_id": encounters.json()["data"][0]["id"],
                "seed": 31,
            },
        )
        state = start.json()["data"]
        index = 0
        while state["status"] == "ACTIVE":
            action = await client.post(
                "/api/v1/combat/action",
                headers={
                    **headers,
                    "Idempotency-Key": f"http-combat-action-{index}",
                },
                json={"combat_id": state["combat_id"], "action_type": "ATTACK"},
            )
            assert action.status_code == 200
            state = action.json()["data"]
            index += 1
        logs = await client.get(
            f"/api/v1/combat/{state['combat_id']}/log", headers=headers
        )

    assert encounters.status_code == 200
    assert start.status_code == 201
    assert state["status"] == "VICTORY"
    assert logs.status_code == 200
    assert [entry["sequence"] for entry in logs.json()["data"]] == list(
        range(len(logs.json()["data"]))
    )
