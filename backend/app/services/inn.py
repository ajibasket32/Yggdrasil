import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.engines.character import CharacterEngine, CharacterStats
from app.models.idempotency_record import IdempotencyRecord
from app.repositories.gameplay import GameUnitOfWork
from app.repositories.world import WorldUnitOfWork
from app.schemas.world import InnRestResult
from app.services.world import (
    WorldIdempotencyConflict,
    WorldNotFoundError,
    WorldRuleViolation,
)


class InnService:
    """Orchestrate deterministic HP/MP restoration at Inns."""

    INN_STAY_PRICE = 50

    def __init__(self, world_uow: WorldUnitOfWork, game_uow: GameUnitOfWork) -> None:
        self._world_uow = world_uow
        self._game_uow = game_uow
        self._fingerprints: dict[tuple[UUID, str, str], str] = {}

    async def rest(
        self, player_id: UUID, character_id: UUID, npc_id: UUID, key: str
    ) -> InnRestResult:
        operation = "inn.rest"
        payload: dict[str, object] = {
            "character_id": str(character_id),
            "npc_id": str(npc_id),
        }
        async with self._world_uow:
            existing = await self._guard(player_id, key, operation, payload)

            async with self._game_uow:
                character = await self._game_uow.characters.get_owned(
                    player_id, character_id, for_update=True
                )
                if character is None:
                    raise WorldNotFoundError("Character was not found")

                if existing is not None:
                    return InnRestResult(
                        character_id=character.id,
                        hp_restored=existing.response_body["hp_restored"],
                        mp_restored=existing.response_body["mp_restored"],
                        price_paid=existing.response_body["price_paid"],
                        gold_remaining=character.gold,
                        current_hp=character.current_hp,
                        current_mp=character.current_mp,
                    )

                npc = await self._world_uow.world.get_npc(npc_id)
                if npc is None or npc.role != "INNKEEPER":
                    raise WorldNotFoundError("Innkeeper not found")

                if npc.home_location_id != character.current_location_id:
                    raise WorldRuleViolation("Innkeeper is not at your location")

                if character.gold < self.INN_STAY_PRICE:
                    raise WorldRuleViolation("Insufficient gold for staying at the Inn")

                # Calculate max stats
                equipment = await self._game_uow.equipment.list_for_character(
                    character.id
                )
                bonuses: dict[str, int] = {}
                for _, _, _, item in equipment:
                    for name, value in item.base_stats.items():
                        bonuses[name] = bonuses.get(name, 0) + int(value)

                stats = CharacterStats(
                    strength=character.strength,
                    dexterity=character.dexterity,
                    agility=character.agility,
                    vitality=character.vitality,
                    intelligence=character.intelligence,
                    wisdom=character.wisdom,
                    charisma=character.charisma,
                )
                derived = CharacterEngine.derive(stats, bonuses)

                hp_to_restore = derived.max_hp - character.current_hp
                mp_to_restore = derived.max_mp - character.current_mp

                character.current_hp = derived.max_hp
                character.current_mp = derived.max_mp
                character.gold -= self.INN_STAY_PRICE

                await self._record(
                    player_id,
                    key,
                    operation,
                    character.id,
                    {
                        "hp_restored": hp_to_restore,
                        "mp_restored": mp_to_restore,
                        "price_paid": self.INN_STAY_PRICE,
                    },
                )

                return InnRestResult(
                    character_id=character.id,
                    hp_restored=hp_to_restore,
                    mp_restored=mp_to_restore,
                    price_paid=self.INN_STAY_PRICE,
                    gold_remaining=character.gold,
                    current_hp=character.current_hp,
                    current_mp=character.current_mp,
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
