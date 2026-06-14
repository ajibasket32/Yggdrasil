import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.database import session_factory
from app.models.save_game import SaveGame
from app.repositories.save import SaveUnitOfWork
from app.schemas.save import SaveSnapshotV1
from app.services.save import SaveService


@pytest.mark.asyncio
async def test_complete_snapshot_survives_session_restart(
    clean_save_database: None,
) -> None:
    player_id = uuid4()
    character_id = uuid4()
    snapshot = SaveSnapshotV1(
        world_tick=15240,
        character={"level": 31},
        inventory={"items": [{"id": "potion", "quantity": 2}]},
        equipment={"weapon": "staff"},
        world_state={"region": "E-Rantel"},
        quest_state={"active": []},
        npc_state={"known": []},
        faction_state={"relations": {}},
        relationships={"npc": {}},
        journal={"entries": []},
        memories={"events": []},
        dungeon_state={"cleared": []},
    )

    async with session_factory() as first_session:
        created = await SaveService(SaveUnitOfWork(first_session)).create_save(
            player_id,
            character_id,
            "Restart Test",
            "create-restart",
            snapshot,
        )

    async with session_factory() as restarted_session:
        service = SaveService(SaveUnitOfWork(restarted_session))
        loaded = await service.load_save(player_id, created.save_id, "load-restart")

    assert loaded.snapshot == snapshot
    assert loaded.save_version == 1
    assert loaded.world_tick == 15240


@pytest.mark.asyncio
async def test_concurrent_duplicate_request_creates_one_save(
    clean_save_database: None,
) -> None:
    player_id = uuid4()
    character_id = uuid4()

    async def create() -> object:
        async with session_factory() as session:
            return await SaveService(SaveUnitOfWork(session)).create_save(
                player_id,
                character_id,
                "Concurrent",
                "same-idempotency-key",
            )

    first, second = await asyncio.gather(create(), create())

    assert first == second
    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(SaveGame))
    assert count == 1


@pytest.mark.asyncio
async def test_legacy_save_is_migrated_atomically_on_load(
    clean_save_database: None,
) -> None:
    player_id = uuid4()
    legacy_payload = {
        "schema_version": 0,
        "world_tick": 9,
        "character_state": {"level": 2},
        "world": {"location": "Nazarick"},
    }

    async with session_factory() as session:
        legacy = SaveGame(
            player_id=player_id,
            character_id=uuid4(),
            save_name="Legacy",
            save_version=1,
            world_tick=9,
            snapshot_reference=legacy_payload,
            snapshot_checksum=SaveService.checksum(legacy_payload),
            schema_version=0,
            engine_version="0.1.0",
            status="VERIFIED",
        )
        session.add(legacy)
        await session.commit()
        legacy_id = legacy.id

    async with session_factory() as session:
        loaded = await SaveService(SaveUnitOfWork(session)).load_save(
            player_id,
            legacy_id,
            "load-legacy",
        )

    async with session_factory() as session:
        migrated = await session.get(SaveGame, legacy_id)

    assert loaded.snapshot.character == {"level": 2}
    assert loaded.snapshot.world_state == {"location": "Nazarick"}
    assert migrated is not None
    assert migrated.schema_version == 1
    assert migrated.snapshot_checksum == SaveService.checksum(
        migrated.snapshot_reference
    )


@pytest.mark.asyncio
async def test_soft_deleted_save_is_hidden_but_retained(
    clean_save_database: None,
) -> None:
    player_id = uuid4()
    async with session_factory() as session:
        service = SaveService(SaveUnitOfWork(session))
        created = await service.create_save(
            player_id,
            uuid4(),
            "Delete",
            "create-delete",
        )

    async with session_factory() as session:
        result = await SaveService(SaveUnitOfWork(session)).delete_save(
            player_id,
            created.save_id,
            "delete-save",
        )

    async with session_factory() as session:
        service = SaveService(SaveUnitOfWork(session))
        listed = await service.list_saves(player_id)
        retained = await session.get(SaveGame, created.save_id)

    assert result.deleted is True
    assert listed == []
    assert retained is not None
    assert retained.deleted_at is not None
