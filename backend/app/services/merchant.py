import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.engines.inventory import InventoryEngine, InventoryEntry, ItemRule
from app.models.gameplay import InventoryItem
from app.models.idempotency_record import IdempotencyRecord
from app.repositories.gameplay import GameUnitOfWork
from app.repositories.world import WorldUnitOfWork
from app.schemas.world import ShopItemView, ShopPurchaseResult, ShopView
from app.services.world import (
    WorldIdempotencyConflict,
    WorldNotFoundError,
    WorldRuleViolation,
)


class MerchantService:
    """Orchestrate deterministic shop item purchases."""

    def __init__(self, world_uow: WorldUnitOfWork, game_uow: GameUnitOfWork) -> None:
        self._world_uow = world_uow
        self._game_uow = game_uow
        self._fingerprints: dict[tuple[UUID, str, str], str] = {}

    async def get_shop(self, shop_id: UUID) -> ShopView:
        async with self._world_uow:
            shop = await self._world_uow.world.get_shop(shop_id)
            if shop is None:
                raise WorldNotFoundError("Shop was not found")
            items = await self._world_uow.world.list_shop_items(shop.id)
            return ShopView(
                id=shop.id,
                name=shop.name,
                description=shop.description,
                owner_npc_id=shop.owner_npc_id,
                items=[
                    ShopItemView(
                        item_id=item.id,
                        name=item.name,
                        description=item.description,
                        price=shop_item.price,
                        rarity=item.rarity,
                        item_type=item.item_type,
                    )
                    for shop_item, item in items
                ],
            )

    async def purchase_item(
        self,
        player_id: UUID,
        character_id: UUID,
        shop_id: UUID,
        item_id: UUID,
        key: str,
    ) -> ShopPurchaseResult:
        operation = "merchant.purchase"
        payload: dict[str, object] = {
            "character_id": str(character_id),
            "shop_id": str(shop_id),
            "item_id": str(item_id),
        }
        async with self._world_uow:
            # Re-using world_uow's idempotency repository via GameUnitOfWork
            # if they share the session. Actually, let's keep it simple
            # and use world_uow's idempotency.
            existing = await self._guard(player_id, key, operation, payload)

            # Use game_uow for character and inventory updates
            async with self._game_uow:
                character = await self._game_uow.characters.get_owned(
                    player_id, character_id, for_update=True
                )
                if character is None:
                    raise WorldNotFoundError("Character was not found")

                if existing is not None:
                    return ShopPurchaseResult(
                        character_id=character.id,
                        item_id=item_id,
                        price_paid=existing.response_body["price_paid"],
                        gold_remaining=character.gold,
                    )

                shop_item_row = await self._world_uow.world.get_shop_item(
                    shop_id, item_id
                )
                if shop_item_row is None:
                    raise WorldNotFoundError("Item not found in this shop")

                shop_item, item = shop_item_row
                shop = await self._world_uow.world.get_shop(shop_id)
                if shop is None:
                    raise WorldNotFoundError("Shop was not found")

                if character.gold < shop_item.price:
                    raise WorldRuleViolation("Insufficient gold")

                inventory = await self._game_uow.inventory.get_for_character(
                    character.id, for_update=True
                )
                if inventory is None:
                    raise WorldRuleViolation("Character has no inventory")

                entries = await self._game_uow.inventory.list_entries(
                    character.id, for_update=True
                )
                rule = ItemRule(
                    item_id=item.id,
                    weight=float(item.weight),
                    is_stackable=item.is_stackable,
                    max_stack=item.max_stack,
                    is_quest_item=item.is_quest_item,
                    is_droppable=item.is_droppable,
                )

                # We only support quantity 1 for now as per instructions
                quantity = 1
                current_weight = round(
                    sum(float(i.weight) * e.quantity for e, i in entries), 2
                )

                try:
                    updates, creates = InventoryEngine.plan_add(
                        [self._to_engine_entry(e) for e, _ in entries],
                        rule,
                        quantity,
                        slot_count=inventory.slot_count,
                        current_weight=current_weight,
                        max_weight=float(inventory.max_weight),
                    )
                except Exception as e:
                    raise WorldRuleViolation(str(e)) from e

                # Apply updates
                character.gold -= shop_item.price
                await self._world_uow.world.progress_matching(
                    player_id, character, "NPC_HELP", UUID(str(shop_id))
                )
                await self._world_uow.world.progress_matching(
                    player_id, character, "NPC_HELP", UUID(str(shop_item.shop_id))
                )
                # Allow shop buy to count as NPC_HELP for the owner too
                await self._world_uow.world.progress_matching(
                    player_id, character, "NPC_HELP", UUID(str(shop.owner_npc_id))
                )
                for entry_id, new_quantity in updates:
                    entry = next(e for e, _ in entries if e.id == entry_id)
                    entry.quantity = new_quantity

                for planned in creates:
                    await self._game_uow.inventory.add_entry(
                        InventoryItem(
                            inventory_id=inventory.id,
                            item_id=planned.item_id,
                            quantity=planned.quantity,
                            slot_index=planned.slot_index,
                            unique_instance_id=planned.unique_instance_id,
                        )
                    )

                await self._record(
                    player_id,
                    key,
                    operation,
                    character.id,
                    {"price_paid": shop_item.price, "item_id": str(item_id)},
                )

                return ShopPurchaseResult(
                    character_id=character.id,
                    item_id=item_id,
                    price_paid=shop_item.price,
                    gold_remaining=character.gold,
                )

    async def _guard(
        self,
        player_id: UUID,
        key: str,
        operation: str,
        payload: dict[str, object],
    ) -> IdempotencyRecord | None:
        await self._world_uow.lock_key(f"idempotency:{player_id}:{operation}:{key}")
        fingerprint = self._fingerprint(payload)
        self._fingerprints[(player_id, key, operation)] = fingerprint
        existing = await self._world_uow.idempotency.get(player_id, key, operation)
        if existing and existing.request_fingerprint != fingerprint:
            raise WorldIdempotencyConflict(
                "Idempotency key was already used with a different request"
            )
        return existing

    async def _record(
        self,
        player_id: UUID,
        key: str,
        operation: str,
        character_id: UUID,
        extra: dict[str, object],
    ) -> None:
        await self._world_uow.idempotency.add(
            IdempotencyRecord(
                player_id=player_id,
                idempotency_key=key,
                request_fingerprint=self._fingerprints[(player_id, key, operation)],
                operation=operation,
                response_status=200,
                response_body={"character_id": str(character_id), **extra},
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )

    @staticmethod
    def _fingerprint(payload: dict[str, object]) -> str:
        serialized = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), default=str
        )
        return hashlib.sha256(serialized.encode()).hexdigest()

    @staticmethod
    def _to_engine_entry(
        entry: InventoryItem,
    ) -> InventoryEntry:
        return InventoryEntry(
            entry_id=entry.id,
            item_id=entry.item_id,
            quantity=entry.quantity,
            slot_index=entry.slot_index,
            unique_instance_id=entry.unique_instance_id,
        )
