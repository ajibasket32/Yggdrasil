import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from pydantic import JsonValue

from app.core.metrics import (
    CHARACTER_OPERATIONS_TOTAL,
    INVENTORY_OPERATIONS_TOTAL,
    TRAVEL_OPERATIONS_TOTAL,
)
from app.engines.character import (
    CharacterEngine,
    CharacterRuleError,
    CharacterStats,
    ProgressionEngine,
)
from app.engines.equipment import (
    EquipmentCandidate,
    EquipmentEngine,
    EquipmentRuleError,
)
from app.engines.inventory import (
    InventoryEngine,
    InventoryEntry,
    InventoryRuleError,
    ItemRule,
)
from app.engines.navigation import NavigationEngine, NavigationRuleError, TravelRoute
from app.models.gameplay import (
    Character,
    CharacterJob,
    CharacterLocationDiscovery,
    CharacterSkill,
    EquippedItem,
    Inventory,
    InventoryItem,
    Item,
    Location,
)
from app.models.idempotency_record import IdempotencyRecord
from app.repositories.gameplay import GameUnitOfWork
from app.schemas.gameplay import (
    CharacterCreationDefinitions,
    CharacterSheet,
    CharacterSummary,
    CreateCharacterRequest,
    DerivedStatBlock,
    EquipmentItemView,
    EquipmentSlotView,
    EquipmentView,
    InventoryItemView,
    InventoryView,
    JobProgressView,
    JobView,
    LocationView,
    RaceView,
    SkillView,
    StatBlock,
    TravelResult,
)


class GameplayError(Exception):
    """Stable error boundary for v0.5 gameplay services."""

    code = "GAMEPLAY_ERROR"
    status_code = 409


class GameplayNotFoundError(GameplayError):
    code = "GAMEPLAY_NOT_FOUND"
    status_code = 404


class CharacterNotFoundError(GameplayNotFoundError):
    code = "CHARACTER_NOT_FOUND"


class DefinitionNotFoundError(GameplayNotFoundError):
    code = "DEFINITION_NOT_FOUND"


class GameplayConflictError(GameplayError):
    code = "GAMEPLAY_CONFLICT"


class GameplayRuleViolation(GameplayError):
    code = "GAMEPLAY_RULE_VIOLATION"
    status_code = 400


class GameplayIdempotencyConflict(GameplayConflictError):
    code = "IDEMPOTENCY_KEY_REUSED"


class CharacterService:
    """Orchestrate deterministic v0.5 engines and canonical persistence."""

    STARTER_ITEM_NAMES = (
        "Field Potion",
        "Frontier Iron Sword",
        "Traveler Seal",
    )

    def __init__(self, unit_of_work: GameUnitOfWork) -> None:
        self._uow = unit_of_work

    async def creation_definitions(self) -> CharacterCreationDefinitions:
        async with self._uow:
            races = await self._uow.definitions.list_selectable_races()
            jobs = await self._uow.definitions.list_starting_jobs()
            location = await self._uow.definitions.get_starting_location()
            if location is None:
                raise DefinitionNotFoundError("Starting location is not configured")
            return CharacterCreationDefinitions(
                races=[RaceView.model_validate(race) for race in races],
                starting_jobs=[JobView.model_validate(job) for job in jobs],
                starting_location=self._location_view(location, True, True),
            )

    async def create_character(
        self,
        player_id: UUID,
        request: CreateCharacterRequest,
        idempotency_key: str,
    ) -> CharacterSheet:
        operation = "character.create"
        fingerprint = self._fingerprint(request.model_dump(mode="json"))
        async with self._uow:
            await self._uow.lock_key(f"idempotency:{player_id}:{operation}:{idempotency_key}")
            existing = await self._existing_result(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing is not None:
                character = await self._owned(
                    player_id, UUID(str(existing.response_body["character_id"]))
                )
                return await self._sheet(character)

            await self._uow.characters.lock_name(player_id, request.name)
            if await self._uow.characters.name_exists(player_id, request.name):
                raise GameplayConflictError("Character name is already used by this player")
            race = await self._uow.definitions.get_race(request.race_id)
            job = await self._uow.definitions.get_job(request.starting_job_id)
            location = await self._uow.definitions.get_starting_location()
            if race is None or not race.selectable:
                raise DefinitionNotFoundError("Selectable race was not found")
            if job is None or not job.selectable_at_creation or job.tier != "BASIC":
                raise GameplayRuleViolation("Starting job must be a selectable Basic job")
            if location is None:
                raise DefinitionNotFoundError("Starting location is not configured")

            try:
                build = CharacterEngine.create(
                    race.base_stats,
                    race.racial_bonuses,
                    race.racial_penalties,
                    job.stat_modifiers,
                )
            except CharacterRuleError as error:
                raise GameplayRuleViolation(str(error)) from error
            character = Character(
                player_id=player_id,
                name=request.name,
                race_id=race.id,
                active_job_id=job.id,
                current_location_id=location.id,
                gender=request.gender,
                alignment=request.alignment,
                level=1,
                experience=0,
                skill_points=0,
                **build.stats.as_dict(),
                current_hp=build.derived.max_hp,
                current_mp=build.derived.max_mp,
                current_stamina=build.derived.max_stamina,
                gold=100,
                fame=0,
                karma=0,
            )
            await self._uow.characters.add(character)
            await self._uow.characters.add_job(
                CharacterJob(
                    player_id=player_id,
                    character_id=character.id,
                    job_id=job.id,
                    job_level=1,
                    experience=0,
                )
            )
            skills_to_add = [
                CharacterSkill(
                    character_id=character.id,
                    skill_id=unlock.skill_id,
                    skill_level=1,
                )
                for unlock in await self._uow.definitions.list_job_skills(job.id)
                if unlock.required_level <= 1
            ]
            if skills_to_add:
                await self._uow.characters.add_skills(skills_to_add)

            inventory = await self._uow.inventory.add_inventory(
                Inventory(
                    character_id=character.id,
                    slot_count=40,
                    max_weight=100.0,
                )
            )
            starter_items = {
                item.name: item
                for item in await self._uow.definitions.get_named_items(self.STARTER_ITEM_NAMES)
            }
            if set(starter_items) != set(self.STARTER_ITEM_NAMES):
                raise DefinitionNotFoundError("Starter item definitions are incomplete")
            starter_quantities = {
                "Field Potion": 5,
                "Frontier Iron Sword": 1,
                "Traveler Seal": 1,
            }
            for slot_index, name in enumerate(self.STARTER_ITEM_NAMES):
                item = starter_items[name]
                await self._uow.inventory.add_entry(
                    InventoryItem(
                        inventory_id=inventory.id,
                        item_id=item.id,
                        quantity=starter_quantities[name],
                        slot_index=slot_index,
                        unique_instance_id=None if item.is_stackable else uuid4(),
                    )
                )
            await self._uow.navigation.add_discovery(
                CharacterLocationDiscovery(
                    character_id=character.id,
                    location_id=location.id,
                )
            )
            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character.id,
            )
            CHARACTER_OPERATIONS_TOTAL.labels("create", "success").inc()
            return await self._sheet(character)

    async def list_characters(self, player_id: UUID) -> list[CharacterSummary]:
        async with self._uow:
            characters = await self._uow.characters.list_owned(player_id)
            return [await self._summary(character) for character in characters]

    async def get_character(self, player_id: UUID, character_id: UUID) -> CharacterSheet:
        async with self._uow:
            return await self._sheet(await self._owned(player_id, character_id))

    async def award_experience(
        self,
        player_id: UUID,
        character_id: UUID,
        amount: int,
        idempotency_key: str,
    ) -> CharacterSheet:
        operation = "character.award_experience"
        fingerprint = self._fingerprint({"character_id": str(character_id), "amount": amount})
        async with self._uow:
            existing = await self._guard_operation(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing is not None:
                return await self._sheet(await self._owned(player_id, character_id))
            character = await self._owned(player_id, character_id, for_update=True)
            character_job = await self._uow.characters.get_character_job(
                character.id, character.active_job_id, for_update=True
            )
            job = await self._uow.definitions.get_job(character.active_job_id)
            if character_job is None or job is None:
                raise DefinitionNotFoundError("Active job progression is missing")
            unlocks = await self._uow.definitions.list_job_skills(job.id)
            unlocked_ids = await self._uow.characters.skill_ids(character.id)
            result = ProgressionEngine.award_experience(
                level=character.level,
                experience=character.experience,
                job_level=character_job.job_level,
                job_experience=character_job.experience,
                job_max_level=job.max_level,
                skill_points=character.skill_points,
                stats=self._stats(character),
                job_stat_modifiers=job.stat_modifiers,
                skill_unlocks=[(unlock.skill_id, unlock.required_level) for unlock in unlocks],
                already_unlocked=unlocked_ids,
                amount=amount,
            )
            character.level = result.level
            character.experience = result.experience
            character.skill_points = result.skill_points
            self._apply_stats(character, result.stats)
            character_job.job_level = result.job_level
            character_job.experience = result.job_experience
            skills_to_add = [
                CharacterSkill(
                    character_id=character.id,
                    skill_id=skill_id,
                    skill_level=1,
                )
                for skill_id in result.unlocked_skill_ids
            ]
            if skills_to_add:
                await self._uow.characters.add_skills(skills_to_add)

            derived = CharacterEngine.derive(result.stats)
            character.current_hp = derived.max_hp
            character.current_mp = derived.max_mp
            character.current_stamina = derived.max_stamina
            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character.id,
            )
            CHARACTER_OPERATIONS_TOTAL.labels("award_experience", "success").inc()
            return await self._sheet(character)

    async def unlock_job(
        self,
        player_id: UUID,
        character_id: UUID,
        job_id: UUID,
        idempotency_key: str,
    ) -> CharacterSheet:
        operation = "character.unlock_job"
        fingerprint = self._fingerprint({"character_id": str(character_id), "job_id": str(job_id)})
        async with self._uow:
            existing_record = await self._guard_operation(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing_record is not None:
                return await self._sheet(await self._owned(player_id, character_id))
            character = await self._owned(player_id, character_id, for_update=True)
            job = await self._uow.definitions.get_job(job_id)
            if job is None:
                raise DefinitionNotFoundError("Job definition was not found")
            existing = await self._uow.characters.get_character_job(character.id, job.id)
            if existing is None:
                try:
                    eligible = ProgressionEngine.prerequisites_met(
                        job.prerequisites,
                        character_level=character.level,
                        karma=character.karma,
                        race_id=character.race_id,
                        job_levels=await self._uow.characters.job_levels(character.id),
                    )
                except CharacterRuleError as error:
                    raise GameplayRuleViolation(str(error)) from error
                if not eligible:
                    raise GameplayRuleViolation("Job prerequisites are not met")
                await self._uow.characters.add_job(
                    CharacterJob(
                        player_id=player_id,
                        character_id=character.id,
                        job_id=job.id,
                        job_level=1,
                        experience=0,
                    )
                )
                unlocked = await self._uow.characters.skill_ids(character.id)
                skills_to_add = [
                    CharacterSkill(
                        character_id=character.id,
                        skill_id=job_skill.skill_id,
                        skill_level=1,
                    )
                    for job_skill in await self._uow.definitions.list_job_skills(job.id)
                    if job_skill.required_level <= 1 and job_skill.skill_id not in unlocked
                ]
                if skills_to_add:
                    await self._uow.characters.add_skills(skills_to_add)

            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character.id,
            )
            CHARACTER_OPERATIONS_TOTAL.labels("unlock_job", "success").inc()
            return await self._sheet(character)

    async def change_job(
        self,
        player_id: UUID,
        character_id: UUID,
        job_id: UUID,
        idempotency_key: str,
    ) -> CharacterSheet:
        operation = "character.change_job"
        fingerprint = self._fingerprint({"character_id": str(character_id), "job_id": str(job_id)})
        async with self._uow:
            existing_record = await self._guard_operation(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing_record is not None:
                return await self._sheet(await self._owned(player_id, character_id))
            character = await self._owned(player_id, character_id, for_update=True)
            owned_job = await self._uow.characters.get_character_job(character.id, job_id)
            if owned_job is None:
                raise GameplayRuleViolation("Character has not unlocked this job")
            character.active_job_id = job_id
            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character.id,
            )
            CHARACTER_OPERATIONS_TOTAL.labels("change_job", "success").inc()
            return await self._sheet(character)

    async def inventory(self, player_id: UUID, character_id: UUID) -> InventoryView:
        async with self._uow:
            await self._owned(player_id, character_id)
            return await self._inventory_view(character_id)

    async def drop_item(
        self,
        player_id: UUID,
        character_id: UUID,
        inventory_item_id: UUID,
        quantity: int,
        idempotency_key: str,
    ) -> InventoryView:
        operation = "inventory.drop"
        fingerprint = self._fingerprint(
            {
                "character_id": str(character_id),
                "inventory_item_id": str(inventory_item_id),
                "quantity": quantity,
            }
        )
        async with self._uow:
            existing_record = await self._guard_operation(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing_record is not None:
                return await self._inventory_view(character_id)
            await self._owned(player_id, character_id, for_update=True)
            result = await self._uow.inventory.get_entry(
                character_id, inventory_item_id, for_update=True
            )
            if result is None:
                raise GameplayNotFoundError("Inventory item was not found")
            entry, item = result
            if await self._uow.equipment.is_equipped(entry.id):
                raise GameplayRuleViolation("Equipped items must be unequipped first")
            try:
                InventoryEngine.validate_drop(self._entry(entry), self._item_rule(item), quantity)
            except InventoryRuleError as error:
                raise GameplayRuleViolation(str(error)) from error
            if quantity == entry.quantity:
                await self._uow.inventory.delete_entry(entry)
            else:
                entry.quantity -= quantity
            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character_id,
            )
            INVENTORY_OPERATIONS_TOTAL.labels("drop", "success").inc()
            return await self._inventory_view(character_id)

    async def split_stack(
        self,
        player_id: UUID,
        character_id: UUID,
        inventory_item_id: UUID,
        quantity: int,
        idempotency_key: str,
    ) -> InventoryView:
        operation = "inventory.split"
        fingerprint = self._fingerprint(
            {
                "character_id": str(character_id),
                "inventory_item_id": str(inventory_item_id),
                "quantity": quantity,
            }
        )
        async with self._uow:
            existing_record = await self._guard_operation(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing_record is not None:
                return await self._inventory_view(character_id)
            await self._owned(player_id, character_id, for_update=True)
            inventory = await self._inventory_or_error(character_id, for_update=True)
            result = await self._uow.inventory.get_entry(
                character_id, inventory_item_id, for_update=True
            )
            entries = await self._uow.inventory.list_entries(character_id, for_update=True)
            if result is None:
                raise GameplayNotFoundError("Inventory item was not found")
            entry, item = result
            occupied = {row.slot_index for row, _ in entries}
            free_slot = next(
                (index for index in range(inventory.slot_count) if index not in occupied),
                None,
            )
            try:
                planned = InventoryEngine.split(
                    self._entry(entry), self._item_rule(item), quantity, free_slot
                )
            except InventoryRuleError as error:
                raise GameplayRuleViolation(str(error)) from error
            entry.quantity -= quantity
            await self._uow.inventory.add_entry(
                InventoryItem(
                    inventory_id=inventory.id,
                    item_id=planned.item_id,
                    quantity=planned.quantity,
                    slot_index=planned.slot_index,
                    unique_instance_id=planned.unique_instance_id,
                )
            )
            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character_id,
            )
            INVENTORY_OPERATIONS_TOTAL.labels("split", "success").inc()
            return await self._inventory_view(character_id)

    async def merge_stacks(
        self,
        player_id: UUID,
        character_id: UUID,
        source_id: UUID,
        target_id: UUID,
        idempotency_key: str,
    ) -> InventoryView:
        operation = "inventory.merge"
        fingerprint = self._fingerprint(
            {
                "character_id": str(character_id),
                "source_id": str(source_id),
                "target_id": str(target_id),
            }
        )
        async with self._uow:
            existing_record = await self._guard_operation(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing_record is not None:
                return await self._inventory_view(character_id)
            await self._owned(player_id, character_id, for_update=True)
            source_result = await self._uow.inventory.get_entry(
                character_id, source_id, for_update=True
            )
            target_result = await self._uow.inventory.get_entry(
                character_id, target_id, for_update=True
            )
            if source_result is None or target_result is None:
                raise GameplayNotFoundError("Inventory stack was not found")
            source, source_item = source_result
            target, _ = target_result
            try:
                source_quantity, target_quantity = InventoryEngine.merge(
                    self._entry(source),
                    self._entry(target),
                    self._item_rule(source_item),
                )
            except InventoryRuleError as error:
                raise GameplayRuleViolation(str(error)) from error
            target.quantity = target_quantity
            if source_quantity == 0:
                await self._uow.inventory.delete_entry(source)
            else:
                source.quantity = source_quantity
            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character_id,
            )
            INVENTORY_OPERATIONS_TOTAL.labels("merge", "success").inc()
            return await self._inventory_view(character_id)

    async def sort_inventory(
        self,
        player_id: UUID,
        character_id: UUID,
        idempotency_key: str,
    ) -> InventoryView:
        operation = "inventory.sort"
        fingerprint = self._fingerprint({"character_id": str(character_id)})
        async with self._uow:
            existing_record = await self._guard_operation(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing_record is not None:
                return await self._inventory_view(character_id)
            await self._owned(player_id, character_id, for_update=True)
            inventory = await self._uow.inventory.get_for_character(character_id, for_update=True)
            if inventory is None:
                raise GameplayNotFoundError("Inventory was not found")
            rows = await self._uow.inventory.list_entries(character_id, for_update=True)
            mapping = InventoryEngine.sorted_slots(
                [self._entry(entry) for entry, _ in rows],
                {item.id: item.name for _, item in rows},
            )
            for offset, (entry, _) in enumerate(rows, start=1):
                entry.slot_index = inventory.slot_count + offset
            await self._uow.inventory.flush()
            for entry, _ in rows:
                entry.slot_index = mapping[entry.id]
            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character_id,
            )
            INVENTORY_OPERATIONS_TOTAL.labels("sort", "success").inc()
            return await self._inventory_view(character_id)

    async def equipment(self, player_id: UUID, character_id: UUID) -> EquipmentView:
        async with self._uow:
            await self._owned(player_id, character_id)
            return await self._equipment_view(character_id)

    async def equip(
        self,
        player_id: UUID,
        character_id: UUID,
        inventory_item_id: UUID,
        slot_id: UUID,
        idempotency_key: str,
    ) -> EquipmentView:
        operation = "equipment.equip"
        fingerprint = self._fingerprint(
            {
                "character_id": str(character_id),
                "inventory_item_id": str(inventory_item_id),
                "slot_id": str(slot_id),
            }
        )
        async with self._uow:
            existing_record = await self._guard_operation(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing_record is not None:
                return await self._equipment_view(character_id)
            character = await self._owned(player_id, character_id, for_update=True)
            result = await self._uow.inventory.get_entry(
                character_id, inventory_item_id, for_update=True
            )
            slot = await self._uow.definitions.get_equipment_slot(slot_id)
            if result is None or slot is None:
                raise GameplayNotFoundError("Item or equipment slot was not found")
            entry, item = result
            try:
                EquipmentEngine.validate_equip(
                    EquipmentCandidate(
                        inventory_item_id=entry.id,
                        quantity=entry.quantity,
                        required_level=item.required_level,
                        compatible_slots=tuple(item.compatible_slots),
                    ),
                    slot_code=slot.code,
                    character_level=character.level,
                )
            except EquipmentRuleError as error:
                raise GameplayRuleViolation(str(error)) from error
            current_item_slot = await self._uow.equipment.get_by_inventory_item(
                entry.id, for_update=True
            )
            if current_item_slot is not None and current_item_slot.slot_id != slot.id:
                raise GameplayRuleViolation("Item is already equipped in another slot")
            if current_item_slot is not None:
                await self._record_result(
                    player_id,
                    idempotency_key,
                    operation,
                    fingerprint,
                    character.id,
                )
                INVENTORY_OPERATIONS_TOTAL.labels("equip", "success").inc()
                return await self._equipment_view(character.id)
            occupied = await self._uow.equipment.get_slot(character.id, slot.id, for_update=True)
            if occupied is not None:
                await self._uow.equipment.delete(occupied)
            await self._uow.equipment.add(
                EquippedItem(
                    character_id=character.id,
                    slot_id=slot.id,
                    inventory_item_id=entry.id,
                )
            )
            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character.id,
            )
            INVENTORY_OPERATIONS_TOTAL.labels("equip", "success").inc()
            return await self._equipment_view(character.id)

    async def unequip(
        self,
        player_id: UUID,
        character_id: UUID,
        slot_id: UUID,
        idempotency_key: str,
    ) -> EquipmentView:
        operation = "equipment.unequip"
        fingerprint = self._fingerprint(
            {"character_id": str(character_id), "slot_id": str(slot_id)}
        )
        async with self._uow:
            existing_record = await self._guard_operation(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing_record is not None:
                return await self._equipment_view(character_id)
            await self._owned(player_id, character_id, for_update=True)
            equipped = await self._uow.equipment.get_slot(character_id, slot_id, for_update=True)
            if equipped is not None:
                await self._uow.equipment.delete(equipped)
            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character_id,
            )
            INVENTORY_OPERATIONS_TOTAL.labels("unequip", "success").inc()
            return await self._equipment_view(character_id)

    async def locations(self, player_id: UUID, character_id: UUID) -> list[LocationView]:
        async with self._uow:
            character = await self._owned(player_id, character_id)
            return await self._location_views(character)

    async def travel(
        self,
        player_id: UUID,
        character_id: UUID,
        destination_id: UUID,
        idempotency_key: str,
    ) -> TravelResult:
        operation = "character.travel"
        fingerprint = self._fingerprint(
            {
                "character_id": str(character_id),
                "destination_id": str(destination_id),
            }
        )
        async with self._uow:
            existing_record = await self._guard_operation(
                player_id, idempotency_key, operation, fingerprint
            )
            if existing_record is not None:
                origin_id = UUID(str(existing_record.response_body["origin_id"]))
                saved_destination_id = UUID(str(existing_record.response_body["destination_id"]))
                origin = await self._uow.definitions.get_location(origin_id)
                destination = await self._uow.definitions.get_location(saved_destination_id)
                if origin is None or destination is None:
                    raise DefinitionNotFoundError(
                        "Stored travel result references a missing location"
                    )
                return TravelResult(
                    character_id=character_id,
                    origin=self._location_view(origin, True, True),
                    destination=self._location_view(destination, True, True),
                    newly_discovered=bool(existing_record.response_body["newly_discovered"]),
                )
            character = await self._owned(player_id, character_id, for_update=True)
            origin = await self._uow.definitions.get_location(character.current_location_id)
            destination = await self._uow.definitions.get_location(destination_id)
            if origin is None or destination is None:
                raise DefinitionNotFoundError("Travel location was not found")
            routes = await self._uow.definitions.list_routes_from(origin.id)
            try:
                NavigationEngine.validate_travel(
                    origin.id,
                    destination.id,
                    [
                        TravelRoute(
                            route.origin_location_id,
                            route.destination_location_id,
                            route.requirements,
                        )
                        for route in routes
                    ],
                    character_level=character.level,
                )
            except NavigationRuleError as error:
                TRAVEL_OPERATIONS_TOTAL.labels("rejected").inc()
                raise GameplayRuleViolation(str(error)) from error
            discovered = await self._uow.navigation.discovered_ids(character.id)
            newly_discovered = destination.id not in discovered
            if newly_discovered:
                await self._uow.navigation.add_discovery(
                    CharacterLocationDiscovery(
                        character_id=character.id,
                        location_id=destination.id,
                    )
                )
            character.current_location_id = destination.id
            await self._record_result(
                player_id,
                idempotency_key,
                operation,
                fingerprint,
                character.id,
                {
                    "origin_id": str(origin.id),
                    "destination_id": str(destination.id),
                    "newly_discovered": newly_discovered,
                },
            )
            TRAVEL_OPERATIONS_TOTAL.labels("success").inc()
            return TravelResult(
                character_id=character.id,
                origin=self._location_view(origin, True, True),
                destination=self._location_view(destination, True, True),
                newly_discovered=newly_discovered,
            )

    async def _owned(
        self, player_id: UUID, character_id: UUID, *, for_update: bool = False
    ) -> Character:
        character = await self._uow.characters.get_owned(
            player_id, character_id, for_update=for_update
        )
        if character is None:
            raise CharacterNotFoundError("Character was not found")
        return character

    async def _inventory_or_error(
        self, character_id: UUID, *, for_update: bool = False
    ) -> Inventory:
        inventory = await self._uow.inventory.get_for_character(character_id, for_update=for_update)
        if inventory is None:
            raise GameplayNotFoundError("Character inventory was not found")
        return inventory

    async def _summary(self, character: Character) -> CharacterSummary:
        race = await self._uow.definitions.get_race(character.race_id)
        job = await self._uow.definitions.get_job(character.active_job_id)
        location = await self._uow.definitions.get_location(character.current_location_id)
        if race is None or job is None or location is None:
            raise DefinitionNotFoundError("Character definition reference is missing")
        return CharacterSummary(
            id=character.id,
            name=character.name,
            race=RaceView.model_validate(race),
            level=character.level,
            current_job=JobView.model_validate(job),
            current_location=self._location_view(location, True, True),
            created_at=character.created_at,
        )

    async def _sheet(self, character: Character) -> CharacterSheet:
        summary = await self._summary(character)
        jobs = await self._uow.characters.list_jobs(character.id)
        skills = await self._uow.characters.list_skills(character.id)
        equipment = await self._uow.equipment.list_for_character(character.id)
        bonuses: dict[str, int] = {}
        for _, _, _, item in equipment:
            for name, value in item.base_stats.items():
                bonuses[name] = bonuses.get(name, 0) + int(value)
        derived = CharacterEngine.derive(self._stats(character), bonuses)
        return CharacterSheet(
            **summary.model_dump(),
            gender=character.gender,
            alignment=character.alignment,
            experience=character.experience,
            experience_to_next=ProgressionEngine.experience_to_next(character.level),
            skill_points=character.skill_points,
            stats=StatBlock(**self._stats(character).as_dict()),
            derived_stats=DerivedStatBlock(**derived.__dict__),
            current_hp=character.current_hp,
            current_mp=character.current_mp,
            current_stamina=character.current_stamina,
            gold=character.gold,
            fame=character.fame,
            karma=character.karma,
            jobs=[
                JobProgressView(
                    job=JobView.model_validate(job),
                    job_level=character_job.job_level,
                    experience=character_job.experience,
                    experience_to_next=ProgressionEngine.job_experience_to_next(
                        character_job.job_level
                    ),
                    active=job.id == character.active_job_id,
                )
                for character_job, job in jobs
            ],
            skills=[
                SkillView.model_validate(skill).model_copy(
                    update={"skill_level": character_skill.skill_level}
                )
                for character_skill, skill in skills
            ],
        )

    async def _inventory_view(self, character_id: UUID) -> InventoryView:
        inventory = await self._inventory_or_error(character_id)
        rows = await self._uow.inventory.list_entries(character_id)
        equipped = {
            row.inventory_item_id
            for row, _, _, _ in await self._uow.equipment.list_for_character(character_id)
        }
        rules = {item.id: self._item_rule(item) for _, item in rows}
        entries = [self._entry(entry) for entry, _ in rows]
        return InventoryView(
            inventory_id=inventory.id,
            slot_count=inventory.slot_count,
            used_slots=len(rows),
            total_weight=InventoryEngine.total_weight(entries, rules),
            max_weight=float(inventory.max_weight),
            items=[
                InventoryItemView(
                    inventory_item_id=entry.id,
                    item_id=item.id,
                    name=item.name,
                    item_type=item.item_type,
                    rarity=item.rarity,
                    weight=float(item.weight),
                    value=item.base_value,
                    quantity=entry.quantity,
                    slot_index=entry.slot_index,
                    is_quest_item=item.is_quest_item,
                    is_droppable=item.is_droppable,
                    is_equipped=entry.id in equipped,
                )
                for entry, item in rows
            ],
        )

    async def _equipment_view(self, character_id: UUID) -> EquipmentView:
        slots = await self._uow.definitions.list_equipment_slots()
        equipped = await self._uow.equipment.list_for_character(character_id)
        by_slot = {slot.id: (entry, item) for _, slot, entry, item in equipped}
        bonuses: dict[str, int] = {}
        for _, item in by_slot.values():
            for name, value in item.base_stats.items():
                bonuses[name] = bonuses.get(name, 0) + int(value)
        return EquipmentView(
            slots=[
                EquipmentSlotView(
                    slot_id=slot.id,
                    code=slot.code,
                    name=slot.name,
                    item=(
                        EquipmentItemView(
                            inventory_item_id=by_slot[slot.id][0].id,
                            item_id=by_slot[slot.id][1].id,
                            name=by_slot[slot.id][1].name,
                            base_stats=by_slot[slot.id][1].base_stats,
                        )
                        if slot.id in by_slot
                        else None
                    ),
                )
                for slot in slots
            ],
            total_equipment_bonuses=bonuses,
        )

    async def _location_views(self, character: Character) -> list[LocationView]:
        locations = await self._uow.definitions.list_locations()
        discovered = await self._uow.navigation.discovered_ids(character.id)
        routes = await self._uow.definitions.list_routes_from(character.current_location_id)
        reachable = {route.destination_location_id for route in routes}
        return [
            self._location_view(
                location,
                location.id in discovered,
                location.id in reachable or location.id == character.current_location_id,
            )
            for location in locations
        ]

    async def _guard_operation(
        self,
        player_id: UUID,
        idempotency_key: str,
        operation: str,
        fingerprint: str,
    ) -> IdempotencyRecord | None:
        await self._uow.lock_key(f"idempotency:{player_id}:{operation}:{idempotency_key}")
        return await self._existing_result(player_id, idempotency_key, operation, fingerprint)

    async def _existing_result(
        self,
        player_id: UUID,
        idempotency_key: str,
        operation: str,
        fingerprint: str,
    ) -> IdempotencyRecord | None:
        existing = await self._uow.idempotency.get(player_id, idempotency_key, operation)
        if existing is None:
            return None
        if existing.request_fingerprint != fingerprint:
            raise GameplayIdempotencyConflict(
                "Idempotency key was already used with a different request"
            )
        return existing

    async def _record_result(
        self,
        player_id: UUID,
        key: str,
        operation: str,
        fingerprint: str,
        character_id: UUID,
        extra: dict[str, JsonValue] | None = None,
    ) -> None:
        await self._uow.idempotency.add(
            IdempotencyRecord(
                player_id=player_id,
                idempotency_key=key,
                request_fingerprint=fingerprint,
                operation=operation,
                response_status=200,
                response_body={
                    "character_id": str(character_id),
                    **(extra or {}),
                },
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )

    @staticmethod
    def _stats(character: Character) -> CharacterStats:
        return CharacterStats(
            strength=character.strength,
            dexterity=character.dexterity,
            agility=character.agility,
            vitality=character.vitality,
            intelligence=character.intelligence,
            wisdom=character.wisdom,
            charisma=character.charisma,
        )

    @staticmethod
    def _apply_stats(character: Character, stats: CharacterStats) -> None:
        for name, value in stats.as_dict().items():
            setattr(character, name, value)

    @staticmethod
    def _entry(entry: InventoryItem) -> InventoryEntry:
        return InventoryEntry(
            entry_id=entry.id,
            item_id=entry.item_id,
            quantity=entry.quantity,
            slot_index=entry.slot_index,
            unique_instance_id=entry.unique_instance_id,
        )

    @staticmethod
    def _item_rule(item: Item) -> ItemRule:
        return ItemRule(
            item_id=item.id,
            weight=float(item.weight),
            is_stackable=item.is_stackable,
            max_stack=item.max_stack,
            is_quest_item=item.is_quest_item,
            is_droppable=item.is_droppable,
        )

    @staticmethod
    def _location_view(location: Location, discovered: bool, reachable: bool) -> LocationView:
        return LocationView(
            id=location.id,
            name=location.name,
            location_type=location.location_type,
            description=location.description,
            danger_level=location.danger_level,
            discovered=discovered,
            reachable=reachable,
        )

    @staticmethod
    def _fingerprint(payload: dict[str, JsonValue]) -> str:
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
