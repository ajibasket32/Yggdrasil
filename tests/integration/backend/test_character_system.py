from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.core.database import session_factory
from app.main import app
from app.models.gameplay import Character, InventoryItem
from app.repositories.gameplay import GameStateRepository, GameUnitOfWork
from app.repositories.save import SaveUnitOfWork
from app.schemas.gameplay import CreateCharacterRequest
from app.services.gameplay import CharacterService
from app.services.save import SaveService


import typing
async def _create_character(player_id: UUID, key: str = "create-character") -> typing.Any:
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        definitions = await service.creation_definitions()
        return await service.create_character(
            player_id,
            CreateCharacterRequest(
                name="Aster Vale",
                race_id=definitions.races[0].id,
                gender="Unspecified",
                alignment="NEUTRAL",
                starting_job_id=definitions.starting_jobs[0].id,
            ),
            key,
        )


@pytest.mark.asyncio
async def test_character_creation_is_atomic_complete_and_idempotent(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()

    first = await _create_character(player_id)
    second = await _create_character(player_id)

    assert first == second
    assert len(first.jobs) == 1
    assert len(first.skills) == 1
    async with session_factory() as session:
        character_count = await session.scalar(
            select(func.count()).select_from(Character)
        )
        item_count = await session.scalar(
            select(func.count()).select_from(InventoryItem)
        )
    assert character_count == 1
    assert item_count == 3


@pytest.mark.asyncio
async def test_inventory_equipment_travel_and_save_restore(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    created = await _create_character(player_id)

    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        inventory = await service.inventory(player_id, created.id)
        equipment = await service.equipment(player_id, created.id)
        sword = next(item for item in inventory.items if item.item_type == "WEAPON")
        main_hand = next(slot for slot in equipment.slots if slot.code == "main_hand")
        equipped = await service.equip(
            player_id,
            created.id,
            sword.inventory_item_id,
            main_hand.slot_id,
            "equip-sword",
        )
        equipped_again = await service.equip(
            player_id,
            created.id,
            sword.inventory_item_id,
            main_hand.slot_id,
            "equip-sword-again",
        )
        sorted_inventory = await service.sort_inventory(
            player_id,
            created.id,
            "sort-starter-inventory",
        )
    assert next(slot for slot in equipped.slots if slot.code == "main_hand").item
    assert next(slot for slot in equipped_again.slots if slot.code == "main_hand").item
    assert [item.slot_index for item in sorted_inventory.items] == list(
        range(len(sorted_inventory.items))
    )

    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        locations = await service.locations(player_id, created.id)
        destination = next(
            location
            for location in locations
            if location.reachable and location.id != created.current_location.id
        )
        await service.travel(
            player_id, created.id, destination.id, "travel-before-save"
        )

    async with session_factory() as session:
        save_service = SaveService(
            SaveUnitOfWork(session), GameStateRepository(session)
        )
        save = await save_service.create_save(
            player_id, created.id, "Canonical", "create-canonical-save"
        )

    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        inventory = await service.inventory(player_id, created.id)
        potion = next(item for item in inventory.items if item.name == "Field Potion")
        await service.drop_item(
            player_id,
            created.id,
            potion.inventory_item_id,
            2,
            "drop-after-save",
        )
        locations = await service.locations(player_id, created.id)
        return_location = next(
            location
            for location in locations
            if location.reachable and location.id != destination.id
        )
        await service.travel(
            player_id, created.id, return_location.id, "travel-after-save"
        )

    async with session_factory() as session:
        loaded = await SaveService(
            SaveUnitOfWork(session), GameStateRepository(session)
        ).load_save(player_id, save.save_id, "load-canonical-save")
    assert loaded.snapshot.character["id"] == str(created.id)

    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        restored = await service.get_character(player_id, created.id)
        inventory = await service.inventory(player_id, created.id)
        equipment = await service.equipment(player_id, created.id)
    assert restored.current_location.id == destination.id
    assert (
        next(item for item in inventory.items if item.name == "Field Potion").quantity
        == 5
    )
    assert next(slot for slot in equipment.slots if slot.code == "main_hand").item


@pytest.mark.asyncio
async def test_character_http_creation_and_inspection_flow(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        definitions_response = await client.get("/api/v1/character-definitions")
        definitions = definitions_response.json()["data"]
        create_response = await client.post(
            "/api/v1/characters",
            headers={
                "X-Player-ID": str(player_id),
                "Idempotency-Key": "http-create",
            },
            json={
                "name": "Mira Ash",
                "race_id": definitions["races"][0]["id"],
                "gender": "Female",
                "alignment": "GOOD",
                "starting_job_id": definitions["starting_jobs"][0]["id"],
            },
        )
        character_id = create_response.json()["data"]["id"]
        sheet_response = await client.get(
            f"/api/v1/characters/{character_id}",
            headers={"X-Player-ID": str(player_id)},
        )
        inventory_response = await client.get(
            f"/api/v1/characters/{character_id}/inventory",
            headers={"X-Player-ID": str(player_id)},
        )

    assert definitions_response.status_code == 200
    assert create_response.status_code == 201
    assert sheet_response.status_code == 200
    assert sheet_response.json()["data"]["name"] == "Mira Ash"
    assert len(inventory_response.json()["data"]["items"]) == 3
