import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Literal, cast
from uuid import UUID

from pydantic import JsonValue

from app.core.metrics import COMBAT_ACTIONS_TOTAL, COMBAT_ENCOUNTERS_TOTAL
from app.engines.character import CharacterEngine, CharacterStats, ProgressionEngine
from app.engines.combat import (
    CombatAction,
    CombatantState,
    CombatEngine,
    CombatRuleError,
    StatusEffectState,
)
from app.engines.inventory import InventoryEngine, InventoryEntry, ItemRule
from app.models.combat import (
    CombatEncounter,
    CombatLogEntry,
    CombatParticipant,
    GameOutboxEvent,
    Monster,
)
from app.models.gameplay import Character, CharacterSkill, InventoryItem, Item, Skill
from app.models.idempotency_record import IdempotencyRecord
from app.repositories.combat import CombatUnitOfWork
from app.schemas.combat import (
    CombatActionRequest,
    CombatLogView,
    CombatParticipantView,
    CombatRewardView,
    CombatStateView,
    EncounterDefinitionView,
    StartCombatRequest,
    StatusEffectView,
)
from app.services.gameplay import (
    CharacterNotFoundError,
    DefinitionNotFoundError,
    GameplayConflictError,
    GameplayIdempotencyConflict,
    GameplayNotFoundError,
    GameplayRuleViolation,
)


class CombatNotFoundError(GameplayNotFoundError):
    code = "COMBAT_NOT_FOUND"


class CombatConflictError(GameplayConflictError):
    code = "COMBAT_CONFLICT"


class CombatService:
    """Orchestrate engine-owned combat and atomic rewards."""

    def __init__(self, unit_of_work: CombatUnitOfWork) -> None:
        self._uow = unit_of_work

    async def available_encounters(
        self, player_id: UUID, character_id: UUID
    ) -> list[EncounterDefinitionView]:
        async with self._uow:
            character = await self._owned_character(player_id, character_id)
            rows = await self._uow.combat.list_definitions(
                character.current_location_id
            )
            return [
                EncounterDefinitionView(
                    id=definition.id,
                    name=definition.name,
                    monster_name=monster.name,
                    monster_level=monster.level,
                    difficulty=definition.difficulty,
                    location_id=definition.location_id,
                    reward_experience=monster.reward_experience,
                    reward_gold=monster.reward_gold,
                )
                for definition, monster in rows
            ]

    async def start(
        self,
        player_id: UUID,
        request: StartCombatRequest,
        idempotency_key: str,
    ) -> CombatStateView:
        operation = "combat.start"
        fingerprint = self._fingerprint(request.model_dump(mode="json"))
        async with self._uow:
            existing = await self._guard(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing is not None:
                return await self._view(
                    await self._owned_encounter(
                        player_id, UUID(str(existing.response_body["combat_id"]))
                    )
                )
            character = await self._owned_character(
                player_id, request.character_id, for_update=True
            )
            if character.current_hp <= 0:
                raise GameplayRuleViolation("Character must recover before combat")
            if (
                await self._uow.combat.active_for_character(
                    character.id, for_update=True
                )
                is not None
            ):
                raise CombatConflictError("Character already has an active combat")
            definition_row = await self._uow.combat.get_definition(
                request.encounter_definition_id
            )
            if definition_row is None:
                raise DefinitionNotFoundError("Encounter definition was not found")
            definition, monster = definition_row
            if definition.location_id != character.current_location_id:
                raise GameplayRuleViolation(
                    "Encounter is not available at the current location"
                )

            player_state = await self._player_state(character)
            enemy_state = self._monster_state(monster)
            encounter = await self._uow.combat.add_encounter(
                CombatEncounter(
                    player_id=player_id,
                    character_id=character.id,
                    encounter_definition_id=definition.id,
                    seed=request.seed,
                    status="ACTIVE",
                    round_number=1,
                    action_sequence=0,
                    turn_order=[],
                    rewards={},
                    rewards_applied=False,
                )
            )
            player = await self._uow.combat.add_participant(
                self._participant(encounter.id, "CHARACTER", character.id, player_state)
            )
            enemy = await self._uow.combat.add_participant(
                self._participant(encounter.id, "MONSTER", monster.id, enemy_state)
            )
            encounter.turn_order = [
                str(value)
                for value in CombatEngine.turn_order(
                    [
                        self._state(player),
                        self._state(enemy),
                    ]
                )
            ]
            await self._log(
                encounter,
                None,
                None,
                "START",
                f"Combat begins: {character.name} faces {monster.name}.",
                {"seed": request.seed, "turn_order": encounter.turn_order},
            )
            await self._event(
                encounter,
                "combat.started",
                f"combat:{encounter.id}:started",
                {"character_id": str(character.id), "monster_id": str(monster.id)},
            )
            await self._record(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                encounter.id,
            )
            await self._advance_enemies(encounter, monster, character)
            COMBAT_ENCOUNTERS_TOTAL.labels("started").inc()
            return await self._view(encounter, definition.name)

    async def act(
        self,
        player_id: UUID,
        request: CombatActionRequest,
        idempotency_key: str,
    ) -> CombatStateView:
        operation = "combat.action"
        fingerprint = self._fingerprint(request.model_dump(mode="json"))
        async with self._uow:
            existing = await self._guard(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing is not None:
                return await self._view(
                    await self._owned_encounter(player_id, request.combat_id)
                )
            encounter = await self._owned_encounter(
                player_id, request.combat_id, for_update=True
            )
            if encounter.status != "ACTIVE":
                raise CombatConflictError("Combat is already complete")
            participants = await self._uow.combat.participants(
                encounter.id, for_update=True
            )
            player = self._by_side(participants, "PLAYER")
            enemy = self._by_side(participants, "ENEMY")
            if self._next_actor(encounter) != player.id:
                raise CombatConflictError("It is not the player's turn")
            character = await self._owned_character(
                player_id, encounter.character_id, for_update=True
            )
            action = await self._player_action(request, character, player, enemy)
            await self._resolve_turn(
                encounter,
                player,
                player if action.action_type == "ITEM" else enemy,
                action,
            )
            character.current_hp = player.current_hp
            character.current_mp = player.current_mp
            character.current_stamina = player.current_stamina
            if enemy.current_hp <= 0:
                await self._complete_victory(encounter, character, enemy)
            else:
                definition_row = await self._uow.combat.get_definition(
                    encounter.encounter_definition_id
                )
                if definition_row is None:
                    raise DefinitionNotFoundError("Encounter definition was not found")
                await self._advance_enemies(encounter, definition_row[1], character)
            await self._record(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                encounter.id,
            )
            return await self._view(encounter)

    async def flee(
        self,
        player_id: UUID,
        combat_id: UUID,
        idempotency_key: str,
    ) -> CombatStateView:
        operation = "combat.flee"
        fingerprint = self._fingerprint({"combat_id": str(combat_id)})
        async with self._uow:
            existing = await self._guard(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing is not None:
                return await self._view(
                    await self._owned_encounter(player_id, combat_id)
                )
            encounter = await self._owned_encounter(
                player_id, combat_id, for_update=True
            )
            if encounter.status != "ACTIVE":
                raise CombatConflictError("Combat is already complete")
            participants = await self._uow.combat.participants(
                encounter.id, for_update=True
            )
            player = self._by_side(participants, "PLAYER")
            enemy = self._by_side(participants, "ENEMY")
            if self._next_actor(encounter) != player.id:
                raise CombatConflictError("It is not the player's turn")
            definition_row = await self._uow.combat.get_definition(
                encounter.encounter_definition_id
            )
            if definition_row is None:
                raise DefinitionNotFoundError("Encounter definition was not found")
            success = CombatEngine.escape_succeeds(
                self._state(player),
                self._state(enemy),
                seed=encounter.seed,
                sequence=encounter.action_sequence,
                escape_blocked=definition_row[1].escape_blocked,
            )
            await self._log(
                encounter,
                player,
                enemy,
                "ESCAPE",
                (
                    f"{player.name} escapes combat."
                    if success
                    else f"{player.name} fails to escape."
                ),
                {"success": success},
            )
            encounter.action_sequence += 1
            if success:
                encounter.status = "FLED"
                encounter.completed_at = datetime.now(UTC)
                await self._event(
                    encounter,
                    "combat.ended",
                    f"combat:{encounter.id}:ended",
                    {"status": "FLED"},
                )
                COMBAT_ENCOUNTERS_TOTAL.labels("fled").inc()
            else:
                self._advance_round(encounter)
                character = await self._owned_character(
                    player_id, encounter.character_id, for_update=True
                )
                await self._advance_enemies(
                    encounter,
                    definition_row[1],
                    character,
                )
                character.current_hp = player.current_hp
                character.current_mp = player.current_mp
                character.current_stamina = player.current_stamina
            await self._record(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                encounter.id,
            )
            return await self._view(encounter)

    async def get(self, player_id: UUID, combat_id: UUID) -> CombatStateView:
        async with self._uow:
            return await self._view(await self._owned_encounter(player_id, combat_id))

    async def logs(self, player_id: UUID, combat_id: UUID) -> list[CombatLogView]:
        async with self._uow:
            await self._owned_encounter(player_id, combat_id)
            return [
                CombatLogView.model_validate(row)
                for row in await self._uow.combat.logs(combat_id)
            ]

    async def _advance_enemies(
        self, encounter: CombatEncounter, monster: Monster, character: Character
    ) -> None:
        while encounter.status == "ACTIVE":
            participants = await self._uow.combat.participants(
                encounter.id, for_update=True
            )
            player = self._by_side(participants, "PLAYER")
            enemy = self._by_side(participants, "ENEMY")
            if self._next_actor(encounter) != enemy.id:
                break
            action = CombatEngine.enemy_action(
                self._state(enemy),
                self._state(player),
                round_number=encounter.round_number,
                skill_id=monster.id if monster.behavior.get("skill") else None,
            )
            await self._resolve_turn(encounter, enemy, player, action)
            character.current_hp = player.current_hp
            character.current_mp = player.current_mp
            character.current_stamina = player.current_stamina
            if player.current_hp <= 0:
                encounter.status = "DEFEAT"
                encounter.completed_at = datetime.now(UTC)
                character.current_hp = 1
                await self._event(
                    encounter,
                    "combat.ended",
                    f"combat:{encounter.id}:ended",
                    {"status": "DEFEAT"},
                )
                COMBAT_ENCOUNTERS_TOTAL.labels("defeat").inc()

    async def _resolve_turn(
        self,
        encounter: CombatEncounter,
        actor: CombatParticipant,
        target: CombatParticipant,
        action: CombatAction,
    ) -> None:
        turn_start = CombatEngine.begin_turn(self._state(actor))
        self._apply_state(actor, turn_start.combatant)
        if turn_start.log_lines:
            await self._log(
                encounter,
                actor,
                actor,
                "STATUS",
                " ".join(turn_start.log_lines),
                {"can_act": turn_start.can_act},
            )
        if turn_start.combatant.defeated or not turn_start.can_act:
            encounter.action_sequence += 1
            self._advance_round(encounter)
            return
        try:
            result = CombatEngine.resolve_action(
                turn_start.combatant,
                self._state(target),
                action,
                seed=encounter.seed,
                sequence=encounter.action_sequence,
            )
        except CombatRuleError as error:
            raise GameplayRuleViolation(str(error)) from error
        self._apply_state(actor, result.actor)
        if target.id != actor.id:
            self._apply_state(target, result.target)
        await self._log(
            encounter,
            actor,
            target,
            action.action_type,
            " ".join(result.log_lines),
            {
                "hit": result.hit,
                "critical": result.critical,
                "damage": result.damage,
                "healing": result.healing,
                "skill_id": str(action.skill_id) if action.skill_id else None,
                "item_id": str(action.item_id) if action.item_id else None,
            },
        )
        await self._event(
            encounter,
            "combat.action_taken",
            f"combat:{encounter.id}:action:{encounter.action_sequence}",
            {
                "actor_id": str(actor.id),
                "target_id": str(target.id),
                "action_type": action.action_type,
                "damage": result.damage,
            },
        )
        COMBAT_ACTIONS_TOTAL.labels(
            actor.side.lower(), action.action_type.lower(), "resolved"
        ).inc()
        encounter.action_sequence += 1
        self._advance_round(encounter)

    async def _player_action(
        self,
        request: CombatActionRequest,
        character: Character,
        player: CombatParticipant,
        enemy: CombatParticipant,
    ) -> CombatAction:
        target_id = request.target_id or enemy.id
        if request.action_type in {"ATTACK", "SKILL"} and target_id != enemy.id:
            raise GameplayRuleViolation("Offensive actions must target the enemy")
        if request.action_type == "ATTACK":
            return CombatAction("ATTACK", target_id=enemy.id)
        if request.action_type == "GUARD":
            return CombatAction("GUARD", target_id=player.id)
        if request.action_type == "WAIT":
            return CombatAction("WAIT", target_id=player.id)
        if request.action_type == "SKILL":
            if request.skill_id is None:
                raise GameplayRuleViolation("Skill action requires a skill")
            rows = await self._uow.characters.list_skills(character.id)
            skill_row = next(
                (
                    (owned, skill)
                    for owned, skill in rows
                    if skill.id == request.skill_id
                ),
                None,
            )
            if skill_row is None:
                raise GameplayRuleViolation("Character has not unlocked this skill")
            skill = skill_row[1]
            if skill.skill_type != "ACTIVE":
                raise GameplayRuleViolation("Passive skills cannot be selected")
            effect = self._skill_effect(skill)
            if effect == "healing":
                return CombatAction(
                    "ITEM",
                    target_id=player.id,
                    skill_id=skill.id,
                    modifier_percent=max(15, player.max_hp // 4),
                    resource_cost=skill.mana_cost,
                    effect=effect,
                )
            if effect == "barrier":
                return CombatAction(
                    "GUARD",
                    target_id=player.id,
                    skill_id=skill.id,
                    resource_cost=skill.mana_cost,
                    effect=effect,
                )
            return CombatAction(
                "SKILL",
                target_id=enemy.id,
                skill_id=skill.id,
                modifier_percent=125,
                resource_cost=skill.mana_cost or 3,
                effect=effect,
            )
        if request.inventory_item_id is None:
            raise GameplayRuleViolation("Item action requires an inventory item")
        row = await self._uow.inventory.get_entry(
            character.id, request.inventory_item_id, for_update=True
        )
        if row is None:
            raise GameplayRuleViolation("Inventory item was not found")
        entry, item = row
        restore_hp = int(item.base_stats.get("restore_hp", 0))
        if item.item_type != "CONSUMABLE" or restore_hp <= 0:
            raise GameplayRuleViolation("Item cannot be used in combat")
        entry.quantity -= 1
        if entry.quantity == 0:
            await self._uow.inventory.delete_entry(entry)
        return CombatAction(
            "ITEM",
            target_id=player.id,
            item_id=entry.id,
            modifier_percent=restore_hp,
        )

    async def _complete_victory(
        self,
        encounter: CombatEncounter,
        character: Character,
        enemy: CombatParticipant,
    ) -> None:
        if encounter.rewards_applied:
            return
        definition_row = await self._uow.combat.get_definition(
            encounter.encounter_definition_id
        )
        if definition_row is None:
            raise DefinitionNotFoundError("Encounter definition was not found")
        monster = definition_row[1]
        reward = CombatEngine.rewards(
            experience=monster.reward_experience,
            gold=monster.reward_gold,
            loot_chance_percent=monster.loot_chance_percent,
            seed=encounter.seed,
        )
        await self._apply_experience(character, reward.experience)
        character.gold += reward.gold
        items: list[str] = []
        if reward.loot_awarded and monster.loot_item_id is not None:
            item = await self._uow.definitions.get_item(monster.loot_item_id)
            if item is None:
                raise DefinitionNotFoundError("Combat loot item was not found")
            await self._add_item(character.id, item, 1)
            items.append(item.name)
        encounter.status = "VICTORY"
        encounter.completed_at = datetime.now(UTC)
        encounter.rewards = {
            "experience": reward.experience,
            "gold": reward.gold,
            "items": items,
        }
        encounter.rewards_applied = True
        character.current_hp = max(
            1,
            self._by_side(
                await self._uow.combat.participants(encounter.id), "PLAYER"
            ).current_hp,
        )
        await self._event(
            encounter,
            "combat.ended",
            f"combat:{encounter.id}:ended",
            {"status": "VICTORY", "rewards": encounter.rewards},
        )
        await self._log(
            encounter,
            None,
            enemy,
            "VICTORY",
            (f"Victory. Gained {reward.experience} XP and {reward.gold} gold."),
            encounter.rewards,
        )
        COMBAT_ENCOUNTERS_TOTAL.labels("victory").inc()

    async def _apply_experience(self, character: Character, amount: int) -> None:
        character_job = await self._uow.characters.get_character_job(
            character.id, character.active_job_id, for_update=True
        )
        job = await self._uow.definitions.get_job(character.active_job_id)
        if character_job is None or job is None:
            raise DefinitionNotFoundError("Active job progression is missing")
        unlocks = await self._uow.definitions.list_job_skills(job.id)
        unlocked = await self._uow.characters.skill_ids(character.id)
        result = ProgressionEngine.award_experience(
            level=character.level,
            experience=character.experience,
            job_level=character_job.job_level,
            job_experience=character_job.experience,
            job_max_level=job.max_level,
            skill_points=character.skill_points,
            stats=CharacterStats(
                strength=character.strength,
                dexterity=character.dexterity,
                agility=character.agility,
                vitality=character.vitality,
                intelligence=character.intelligence,
                wisdom=character.wisdom,
                charisma=character.charisma,
            ),
            job_stat_modifiers=job.stat_modifiers,
            skill_unlocks=[
                (unlock.skill_id, unlock.required_level) for unlock in unlocks
            ],
            already_unlocked=unlocked,
            amount=amount,
        )
        character.level = result.level
        character.experience = result.experience
        character.skill_points = result.skill_points
        for name, value in result.stats.as_dict().items():
            setattr(character, name, value)
        character_job.job_level = result.job_level
        character_job.experience = result.job_experience
        for skill_id in result.unlocked_skill_ids:
            await self._uow.characters.add_skill(
                CharacterSkill(
                    character_id=character.id,
                    skill_id=skill_id,
                    skill_level=1,
                )
            )

    async def _add_item(self, character_id: UUID, item: Item, quantity: int) -> None:
        inventory = await self._uow.inventory.get_for_character(
            character_id, for_update=True
        )
        if inventory is None:
            raise GameplayRuleViolation("Inventory was not found")
        rows = await self._uow.inventory.list_entries(character_id, for_update=True)
        rules = {
            row_item.id: ItemRule(
                item_id=row_item.id,
                weight=float(row_item.weight),
                is_stackable=row_item.is_stackable,
                max_stack=row_item.max_stack,
                is_quest_item=row_item.is_quest_item,
                is_droppable=row_item.is_droppable,
            )
            for _, row_item in rows
        }
        entries = [
            InventoryEntry(
                entry_id=entry.id,
                item_id=entry.item_id,
                quantity=entry.quantity,
                slot_index=entry.slot_index,
                unique_instance_id=entry.unique_instance_id,
            )
            for entry, _ in rows
        ]
        rule = ItemRule(
            item_id=item.id,
            weight=float(item.weight),
            is_stackable=item.is_stackable,
            max_stack=item.max_stack,
            is_quest_item=item.is_quest_item,
            is_droppable=item.is_droppable,
        )
        current_weight = InventoryEngine.total_weight(entries, rules)
        updates, creates = InventoryEngine.plan_add(
            entries,
            rule,
            quantity,
            slot_count=inventory.slot_count,
            current_weight=current_weight,
            max_weight=float(inventory.max_weight),
        )
        by_id = {entry.id: entry for entry, _ in rows}
        for entry_id, next_quantity in updates:
            by_id[entry_id].quantity = next_quantity
        for planned in creates:
            await self._uow.inventory.add_entry(
                InventoryItem(
                    inventory_id=inventory.id,
                    item_id=planned.item_id,
                    quantity=planned.quantity,
                    slot_index=planned.slot_index,
                    unique_instance_id=planned.unique_instance_id,
                )
            )

    async def _player_state(self, character: Character) -> CombatantState:
        equipment = await self._uow.equipment.list_for_character(character.id)
        bonuses: dict[str, int] = {}
        for _, _, _, item in equipment:
            for name, value in item.base_stats.items():
                bonuses[name] = bonuses.get(name, 0) + int(value)
        derived = CharacterEngine.derive(
            CharacterStats(
                strength=character.strength,
                dexterity=character.dexterity,
                agility=character.agility,
                vitality=character.vitality,
                intelligence=character.intelligence,
                wisdom=character.wisdom,
                charisma=character.charisma,
            ),
            bonuses,
        )
        return CombatantState(
            id=character.id,
            name=character.name,
            side="PLAYER",
            level=character.level,
            hp=min(character.current_hp, derived.max_hp),
            max_hp=derived.max_hp,
            mp=min(character.current_mp, derived.max_mp),
            max_mp=derived.max_mp,
            stamina=min(character.current_stamina, derived.max_stamina),
            max_stamina=derived.max_stamina,
            physical_attack=derived.physical_attack,
            physical_defense=derived.physical_defense,
            magic_attack=derived.magic_attack,
            magic_defense=derived.magic_defense,
            accuracy=derived.accuracy,
            evasion=derived.evasion,
            critical_chance=derived.critical_chance,
            initiative=derived.initiative,
        )

    @staticmethod
    def _monster_state(monster: Monster) -> CombatantState:
        stats = monster.combat_stats
        return CombatantState(
            id=monster.id,
            name=monster.name,
            side="ENEMY",
            level=monster.level,
            hp=monster.max_hp,
            max_hp=monster.max_hp,
            mp=monster.max_mp,
            max_mp=monster.max_mp,
            stamina=monster.max_stamina,
            max_stamina=monster.max_stamina,
            physical_attack=int(stats["physical_attack"]),
            physical_defense=int(stats["physical_defense"]),
            magic_attack=int(stats["magic_attack"]),
            magic_defense=int(stats["magic_defense"]),
            accuracy=int(stats["accuracy"]),
            evasion=int(stats["evasion"]),
            critical_chance=float(stats["critical_chance"]),
            initiative=int(stats["initiative"]),
        )

    @staticmethod
    def _participant(
        encounter_id: UUID,
        source_type: str,
        source_id: UUID,
        state: CombatantState,
    ) -> CombatParticipant:
        return CombatParticipant(
            encounter_id=encounter_id,
            source_type=source_type,
            source_id=source_id,
            name=state.name,
            side=state.side,
            level=state.level,
            current_hp=state.hp,
            max_hp=state.max_hp,
            current_mp=state.mp,
            max_mp=state.max_mp,
            current_stamina=state.stamina,
            max_stamina=state.max_stamina,
            combat_stats={
                "physical_attack": state.physical_attack,
                "physical_defense": state.physical_defense,
                "magic_attack": state.magic_attack,
                "magic_defense": state.magic_defense,
                "accuracy": state.accuracy,
                "evasion": state.evasion,
                "critical_chance": state.critical_chance,
                "initiative": state.initiative,
            },
            statuses=[],
            guarding=False,
        )

    @staticmethod
    def _state(row: CombatParticipant) -> CombatantState:
        stats = row.combat_stats
        return CombatantState(
            id=row.id,
            name=row.name,
            side="PLAYER" if row.side == "PLAYER" else "ENEMY",
            level=row.level,
            hp=row.current_hp,
            max_hp=row.max_hp,
            mp=row.current_mp,
            max_mp=row.max_mp,
            stamina=row.current_stamina,
            max_stamina=row.max_stamina,
            physical_attack=int(stats["physical_attack"]),
            physical_defense=int(stats["physical_defense"]),
            magic_attack=int(stats["magic_attack"]),
            magic_defense=int(stats["magic_defense"]),
            accuracy=int(stats["accuracy"]),
            evasion=int(stats["evasion"]),
            critical_chance=float(stats["critical_chance"]),
            initiative=int(stats["initiative"]),
            guarding=row.guarding,
            statuses=tuple(
                StatusEffectState(
                    code=str(value["code"]),
                    duration=int(value["duration"]),
                    potency=int(value["potency"]),
                )
                for value in row.statuses
            ),
        )

    @staticmethod
    def _apply_state(row: CombatParticipant, state: CombatantState) -> None:
        row.current_hp = state.hp
        row.current_mp = state.mp
        row.current_stamina = state.stamina
        row.guarding = state.guarding
        row.statuses = [
            {
                "code": status.code,
                "duration": status.duration,
                "potency": status.potency,
            }
            for status in state.statuses
        ]

    @staticmethod
    def _by_side(participants: list[CombatParticipant], side: str) -> CombatParticipant:
        return next(row for row in participants if row.side == side)

    @staticmethod
    def _next_actor(encounter: CombatEncounter) -> UUID:
        if not encounter.turn_order:
            raise CombatConflictError("Combat turn order is empty")
        return UUID(
            encounter.turn_order[encounter.action_sequence % len(encounter.turn_order)]
        )

    @staticmethod
    def _advance_round(encounter: CombatEncounter) -> None:
        if encounter.action_sequence % len(encounter.turn_order) == 0:
            encounter.round_number += 1

    async def _log(
        self,
        encounter: CombatEncounter,
        actor: CombatParticipant | None,
        target: CombatParticipant | None,
        action_type: str,
        text: str,
        outcome: dict[str, object],
    ) -> None:
        logs = await self._uow.combat.logs(encounter.id)
        await self._uow.combat.add_log(
            CombatLogEntry(
                encounter_id=encounter.id,
                sequence=len(logs),
                round_number=encounter.round_number,
                actor_participant_id=actor.id if actor else None,
                target_participant_id=target.id if target else None,
                action_type=action_type,
                outcome=outcome,
                text=text,
            )
        )

    async def _event(
        self,
        encounter: CombatEncounter,
        event_type: str,
        key: str,
        payload: dict[str, object],
    ) -> None:
        await self._uow.combat.add_event(
            GameOutboxEvent(
                event_type=event_type,
                aggregate_type="combat",
                aggregate_id=encounter.id,
                player_id=encounter.player_id,
                payload=payload,
                deduplication_key=key,
            )
        )

    async def _view(
        self, encounter: CombatEncounter, encounter_name: str | None = None
    ) -> CombatStateView:
        if encounter_name is None:
            definition = await self._uow.combat.get_definition(
                encounter.encounter_definition_id
            )
            if definition is None:
                raise DefinitionNotFoundError("Encounter definition was not found")
            encounter_name = definition[0].name
        participants = await self._uow.combat.participants(encounter.id)
        logs = await self._uow.combat.logs(encounter.id)
        rewards = encounter.rewards
        items = rewards.get("items", [])
        return CombatStateView(
            combat_id=encounter.id,
            encounter_name=encounter_name,
            seed=encounter.seed,
            status=cast(
                Literal["ACTIVE", "VICTORY", "DEFEAT", "FLED"],
                encounter.status,
            ),
            round_number=encounter.round_number,
            action_sequence=encounter.action_sequence,
            turn_order=[UUID(value) for value in encounter.turn_order],
            participants=[
                CombatParticipantView(
                    id=row.id,
                    source_id=row.source_id,
                    name=row.name,
                    side="PLAYER" if row.side == "PLAYER" else "ENEMY",
                    level=row.level,
                    current_hp=row.current_hp,
                    max_hp=row.max_hp,
                    current_mp=row.current_mp,
                    max_mp=row.max_mp,
                    current_stamina=row.current_stamina,
                    max_stamina=row.max_stamina,
                    guarding=row.guarding,
                    defeated=row.current_hp <= 0,
                    statuses=[
                        StatusEffectView(
                            code=str(value["code"]),
                            duration=int(value["duration"]),
                            potency=int(value["potency"]),
                        )
                        for value in row.statuses
                    ],
                )
                for row in participants
            ],
            rewards=CombatRewardView(
                experience=self._json_int(rewards.get("experience", 0)),
                gold=self._json_int(rewards.get("gold", 0)),
                items=(
                    [str(value) for value in items] if isinstance(items, list) else []
                ),
            ),
            recent_log=[CombatLogView.model_validate(row) for row in logs[-12:]],
        )

    async def _owned_character(
        self, player_id: UUID, character_id: UUID, *, for_update: bool = False
    ) -> Character:
        character = await self._uow.characters.get_owned(
            player_id, character_id, for_update=for_update
        )
        if character is None:
            raise CharacterNotFoundError("Character was not found")
        return character

    async def _owned_encounter(
        self, player_id: UUID, combat_id: UUID, *, for_update: bool = False
    ) -> CombatEncounter:
        encounter = await self._uow.combat.get_owned(
            player_id, combat_id, for_update=for_update
        )
        if encounter is None:
            raise CombatNotFoundError("Combat was not found")
        return encounter

    async def _guard(
        self,
        player_id: UUID,
        key: str,
        operation: str,
        fingerprint: str,
    ) -> IdempotencyRecord | None:
        await self._uow.lock_key(f"idempotency:{player_id}:{operation}:{key}")
        existing = await self._uow.idempotency.get(player_id, key, operation)
        if existing is not None and existing.request_fingerprint != fingerprint:
            raise GameplayIdempotencyConflict(
                "Idempotency key was already used with a different request"
            )
        return existing

    async def _record(
        self,
        player_id: UUID,
        key: str,
        operation: str,
        fingerprint: str,
        combat_id: UUID,
    ) -> None:
        await self._uow.idempotency.add(
            IdempotencyRecord(
                player_id=player_id,
                idempotency_key=key,
                request_fingerprint=fingerprint,
                operation=operation,
                response_status=200,
                response_body={"combat_id": str(combat_id)},
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )

    @staticmethod
    def _skill_effect(skill: Skill) -> str:
        first = skill.effect_definitions[0] if skill.effect_definitions else {}
        return str(first.get("effect", "physical"))

    @staticmethod
    def _json_int(value: object) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int | float | str):
            return int(value)
        return 0

    @staticmethod
    def _fingerprint(payload: dict[str, JsonValue]) -> str:
        serialized = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
