import typing
from uuid import UUID, uuid4

import pytest

from app.core.database import session_factory
from app.repositories.gameplay import GameUnitOfWork
from app.repositories.world import WorldUnitOfWork
from app.schemas.gameplay import CreateCharacterRequest
from app.services.gameplay import CharacterService
from app.services.merchant import MerchantService
from app.services.world import WorldNotFoundError, WorldRuleViolation


async def _create_test_character(player_id: UUID) -> typing.Any:
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        definitions = await service.creation_definitions()
        warrior = next(v for v in definitions.starting_jobs if v.name == "Warrior")
        character = await service.create_character(
            player_id,
            CreateCharacterRequest(
                name="Merchant Tester",
                race_id=definitions.races[0].id,
                gender="Unspecified",
                alignment="NEUTRAL",
                starting_job_id=warrior.id,
            ),
            f"create-{player_id}",
        )
        # Move to Valeris where Silas is
        locations = await service.locations(player_id, character.id)
        valeris = next(v for v in locations if v.name == "Valeris City")
        await service.travel(
            player_id, character.id, valeris.id, f"travel-valeris-{player_id}"
        )
    return character


@pytest.mark.asyncio
async def test_purchase_item_success(clean_gameplay_database: None) -> None:
    player_id = uuid4()
    character = await _create_test_character(player_id)

    async with session_factory() as session:
        world_uow = WorldUnitOfWork(session)
        game_uow = GameUnitOfWork(session)
        merchant_service = MerchantService(world_uow, game_uow)

        hagar = await world_uow.world.get_npc_by_name("Blacksmith Hagar")
        assert hagar is not None
        shop = await world_uow.world.get_shop_by_owner(hagar.id)
        assert shop is not None
        shop_view = await merchant_service.get_shop(shop.id)
        item_to_buy = shop_view.items[0]

        initial_gold = character.gold

        result = await merchant_service.purchase_item(
            player_id, character.id, shop.id, item_to_buy.item_id, "purchase-1"
        )

        assert result.price_paid == item_to_buy.price
        assert result.gold_remaining == initial_gold - item_to_buy.price

        # Verify inventory
        inventory = await game_uow.inventory.list_entries(character.id)
        assert any(e.item_id == item_to_buy.item_id for e, i in inventory)


@pytest.mark.asyncio
async def test_purchase_insufficient_gold(clean_gameplay_database: None) -> None:
    player_id = uuid4()
    character = await _create_test_character(player_id)

    async with session_factory() as session:
        # Manually set gold to 0
        async with GameUnitOfWork(session) as uow:
            char = await uow.characters.get_owned(
                player_id, character.id, for_update=True
            )
            assert char is not None
            char.gold = 0

        world_uow = WorldUnitOfWork(session)
        game_uow = GameUnitOfWork(session)
        merchant_service = MerchantService(world_uow, game_uow)

        hagar = await world_uow.world.get_npc_by_name("Blacksmith Hagar")
        assert hagar is not None
        shop = await world_uow.world.get_shop_by_owner(hagar.id)
        assert shop is not None
        shop_view = await merchant_service.get_shop(shop.id)
        item_to_buy = shop_view.items[0]

        with pytest.raises(WorldRuleViolation, match="Insufficient gold"):
            await merchant_service.purchase_item(
                player_id,
                character.id,
                shop.id,
                item_to_buy.item_id,
                "purchase-fail",
            )


@pytest.mark.asyncio
async def test_purchase_invalid_shop(clean_gameplay_database: None) -> None:
    player_id = uuid4()
    character = await _create_test_character(player_id)

    async with session_factory() as session:
        merchant_service = MerchantService(
            WorldUnitOfWork(session), GameUnitOfWork(session)
        )
        with pytest.raises(WorldNotFoundError, match="Item not found in this shop"):
            await merchant_service.purchase_item(
                player_id, character.id, uuid4(), uuid4(), "purchase-invalid"
            )
