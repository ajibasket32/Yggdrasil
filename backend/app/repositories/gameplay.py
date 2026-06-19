from dataclasses import dataclass, field
from types import TracebackType
from uuid import UUID

from pydantic import JsonValue
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.models.combat import CombatEncounter
from app.models.gameplay import (
    Character,
    CharacterJob,
    CharacterLocationDiscovery,
    CharacterSkill,
    EquipmentSlot,
    EquippedItem,
    Inventory,
    InventoryItem,
    Item,
    Job,
    JobSkill,
    Location,
    LocationRoute,
    Race,
    Skill,
)
from app.repositories.save import IdempotencyRepository
from app.repositories.world import WorldRepository, WorldSnapshot


def _json_int(value: JsonValue) -> int:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise ValueError("Saved numeric value is invalid")
    return int(value)


def _json_float(value: JsonValue) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise ValueError("Saved numeric value is invalid")
    return float(value)


class DefinitionRepository:
    """Read immutable engine-owned gameplay definitions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_selectable_races(self) -> list[Race]:
        result = await self._session.execute(
            select(Race).where(Race.selectable.is_(True)).order_by(Race.name)
        )
        return list(result.scalars().all())

    async def list_starting_jobs(self) -> list[Job]:
        result = await self._session.execute(
            select(Job).where(Job.selectable_at_creation.is_(True)).order_by(Job.name)
        )
        return list(result.scalars().all())

    async def get_race(self, race_id: UUID) -> Race | None:
        return await self._session.get(Race, race_id)

    async def get_job(self, job_id: UUID) -> Job | None:
        return await self._session.get(Job, job_id)

    async def get_starting_location(self) -> Location | None:
        result = await self._session.execute(
            select(Location).where(Location.is_starting_location.is_(True)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_location(self, location_id: UUID) -> Location | None:
        return await self._session.get(Location, location_id)

    async def list_locations(self) -> list[Location]:
        result = await self._session.execute(select(Location).order_by(Location.name))
        return list(result.scalars().all())

    async def list_routes_from(self, location_id: UUID) -> list[LocationRoute]:
        result = await self._session.execute(
            select(LocationRoute).where(LocationRoute.origin_location_id == location_id)
        )
        return list(result.scalars().all())

    async def list_equipment_slots(self) -> list[EquipmentSlot]:
        result = await self._session.execute(
            select(EquipmentSlot).order_by(EquipmentSlot.code)
        )
        return list(result.scalars().all())

    async def get_equipment_slot(self, slot_id: UUID) -> EquipmentSlot | None:
        return await self._session.get(EquipmentSlot, slot_id)

    async def get_item(self, item_id: UUID) -> Item | None:
        return await self._session.get(Item, item_id)

    async def list_items_by_ids(self, item_ids: set[UUID]) -> list[Item]:
        if not item_ids:
            return []
        result = await self._session.execute(select(Item).where(Item.id.in_(item_ids)))
        return list(result.scalars().all())

    async def get_named_items(self, names: tuple[str, ...]) -> list[Item]:
        result = await self._session.execute(
            select(Item).where(Item.name.in_(names)).order_by(Item.name)
        )
        return list(result.scalars().all())

    async def list_job_skills(self, job_id: UUID) -> list[JobSkill]:
        result = await self._session.execute(
            select(JobSkill)
            .where(JobSkill.job_id == job_id)
            .order_by(JobSkill.required_level, JobSkill.skill_id)
        )
        return list(result.scalars().all())


class CharacterRepository:
    """Player-scoped persistence for characters and progression."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock_name(self, player_id: UUID, name: str) -> None:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:value, 0))"),
            {"value": f"character-name:{player_id}:{name.casefold()}"},
        )

    async def name_exists(self, player_id: UUID, name: str) -> bool:
        result = await self._session.execute(
            select(Character.id).where(
                Character.player_id == player_id,
                Character.name.ilike(name),
                Character.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None

    async def add(self, character: Character) -> Character:
        self._session.add(character)
        await self._session.flush()
        return character

    async def get_owned(
        self,
        player_id: UUID,
        character_id: UUID,
        *,
        for_update: bool = False,
    ) -> Character | None:
        """Read one owned active character."""
        statement = select(Character).where(
            Character.id == character_id,
            Character.player_id == player_id,
            Character.deleted_at.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_owned(self, player_id: UUID) -> list[Character]:
        result = await self._session.execute(
            select(Character)
            .where(
                Character.player_id == player_id,
                Character.deleted_at.is_(None),
            )
            .order_by(Character.created_at, Character.id)
        )
        return list(result.scalars().all())

    async def add_job(self, character_job: CharacterJob) -> CharacterJob:
        self._session.add(character_job)
        await self._session.flush()
        return character_job

    async def get_character_job(
        self,
        character_id: UUID,
        job_id: UUID,
        *,
        for_update: bool = False,
    ) -> CharacterJob | None:
        statement = select(CharacterJob).where(
            CharacterJob.character_id == character_id,
            CharacterJob.job_id == job_id,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_jobs(self, character_id: UUID) -> list[tuple[CharacterJob, Job]]:
        result = await self._session.execute(
            select(CharacterJob, Job)
            .join(Job, Job.id == CharacterJob.job_id)
            .where(CharacterJob.character_id == character_id)
            .order_by(Job.tier, Job.name)
        )
        return list(result.tuples().all())

    async def job_levels(self, character_id: UUID) -> dict[UUID, int]:
        result = await self._session.execute(
            select(CharacterJob.job_id, CharacterJob.job_level).where(
                CharacterJob.character_id == character_id
            )
        )
        return {job_id: level for job_id, level in result.tuples().all()}

    async def add_skill(self, character_skill: CharacterSkill) -> CharacterSkill:
        self._session.add(character_skill)
        await self._session.flush()
        return character_skill

    async def add_skills(self, character_skills: list[CharacterSkill]) -> None:
        self._session.add_all(character_skills)
        await self._session.flush()

    async def skill_ids(self, character_id: UUID) -> set[UUID]:
        result = await self._session.execute(
            select(CharacterSkill.skill_id).where(
                CharacterSkill.character_id == character_id
            )
        )
        return set(result.scalars().all())

    async def list_skills(
        self, character_id: UUID
    ) -> list[tuple[CharacterSkill, Skill]]:
        result = await self._session.execute(
            select(CharacterSkill, Skill)
            .join(Skill, Skill.id == CharacterSkill.skill_id)
            .where(CharacterSkill.character_id == character_id)
            .order_by(Skill.name)
        )
        return list(result.tuples().all())


class InventoryRepository:
    """Atomic inventory and item-instance persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_inventory(self, inventory: Inventory) -> Inventory:
        self._session.add(inventory)
        await self._session.flush()
        return inventory

    async def get_for_character(
        self, character_id: UUID, *, for_update: bool = False
    ) -> Inventory | None:
        statement = select(Inventory).where(Inventory.character_id == character_id)
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def add_entry(self, entry: InventoryItem) -> InventoryItem:
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_entries(
        self, character_id: UUID, *, for_update: bool = False
    ) -> list[tuple[InventoryItem, Item]]:
        statement = (
            select(InventoryItem, Item)
            .join(Inventory, Inventory.id == InventoryItem.inventory_id)
            .join(Item, Item.id == InventoryItem.item_id)
            .where(Inventory.character_id == character_id)
            .order_by(InventoryItem.slot_index)
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return list(result.tuples().all())

    async def get_entry(
        self,
        character_id: UUID,
        entry_id: UUID,
        *,
        for_update: bool = False,
    ) -> tuple[InventoryItem, Item] | None:
        statement = (
            select(InventoryItem, Item)
            .join(Inventory, Inventory.id == InventoryItem.inventory_id)
            .join(Item, Item.id == InventoryItem.item_id)
            .where(
                Inventory.character_id == character_id,
                InventoryItem.id == entry_id,
            )
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.tuples().one_or_none()

    async def delete_entry(self, entry: InventoryItem) -> None:
        await self._session.delete(entry)

    async def flush(self) -> None:
        await self._session.flush()


class EquipmentRepository:
    """Persistence for character equipment slots."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, equipped: EquippedItem) -> EquippedItem:
        self._session.add(equipped)
        await self._session.flush()
        return equipped

    async def get_slot(
        self,
        character_id: UUID,
        slot_id: UUID,
        *,
        for_update: bool = False,
    ) -> EquippedItem | None:
        statement = select(EquippedItem).where(
            EquippedItem.character_id == character_id,
            EquippedItem.slot_id == slot_id,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def is_equipped(self, inventory_item_id: UUID) -> bool:
        result = await self._session.execute(
            select(EquippedItem.id).where(
                EquippedItem.inventory_item_id == inventory_item_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_by_inventory_item(
        self, inventory_item_id: UUID, *, for_update: bool = False
    ) -> EquippedItem | None:
        statement = select(EquippedItem).where(
            EquippedItem.inventory_item_id == inventory_item_id
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_character(
        self, character_id: UUID
    ) -> list[tuple[EquippedItem, EquipmentSlot, InventoryItem, Item]]:
        result = await self._session.execute(
            select(EquippedItem, EquipmentSlot, InventoryItem, Item)
            .join(EquipmentSlot, EquipmentSlot.id == EquippedItem.slot_id)
            .join(
                InventoryItem,
                InventoryItem.id == EquippedItem.inventory_item_id,
            )
            .join(Item, Item.id == InventoryItem.item_id)
            .where(EquippedItem.character_id == character_id)
        )
        return list(result.tuples().all())

    async def delete(self, equipped: EquippedItem) -> None:
        await self._session.delete(equipped)
        await self._session.flush()


class NavigationRepository:
    """Persistence for permanent per-character discoveries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def discovered_ids(self, character_id: UUID) -> set[UUID]:
        result = await self._session.execute(
            select(CharacterLocationDiscovery.location_id).where(
                CharacterLocationDiscovery.character_id == character_id
            )
        )
        return set(result.scalars().all())

    async def add_discovery(
        self, discovery: CharacterLocationDiscovery
    ) -> CharacterLocationDiscovery:
        self._session.add(discovery)
        await self._session.flush()
        return discovery


@dataclass(frozen=True)
class CanonicalSnapshot:
    character: dict[str, JsonValue]
    inventory: dict[str, JsonValue]
    equipment: dict[str, JsonValue]
    world_state: dict[str, JsonValue]
    quest_state: dict[str, JsonValue] = field(default_factory=dict)
    npc_state: dict[str, JsonValue] = field(default_factory=dict)
    faction_state: dict[str, JsonValue] = field(default_factory=dict)
    relationships: dict[str, JsonValue] = field(default_factory=dict)
    journal: dict[str, JsonValue] = field(default_factory=dict)
    memories: dict[str, JsonValue] = field(default_factory=dict)
    dungeon_state: dict[str, JsonValue] = field(default_factory=dict)


class GameStateRepository:
    """Capture and restore implemented canonical state inside a save transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_active_combat(self, player_id: UUID, character_id: UUID) -> bool:
        result = await self._session.execute(
            select(CombatEncounter.id).where(
                CombatEncounter.player_id == player_id,
                CombatEncounter.character_id == character_id,
                CombatEncounter.status == "ACTIVE",
            )
        )
        return result.scalar_one_or_none() is not None

    async def capture(
        self, player_id: UUID, character_id: UUID
    ) -> CanonicalSnapshot | None:
        character = await CharacterRepository(self._session).get_owned(
            player_id, character_id, for_update=True
        )
        if character is None:
            return None
        characters = CharacterRepository(self._session)
        inventory_repository = InventoryRepository(self._session)
        equipment_repository = EquipmentRepository(self._session)
        navigation = NavigationRepository(self._session)
        jobs = await characters.list_jobs(character_id)
        skills = await characters.list_skills(character_id)
        inventory = await inventory_repository.get_for_character(
            character_id, for_update=True
        )
        entries = await inventory_repository.list_entries(character_id, for_update=True)
        equipped = await equipment_repository.list_for_character(character_id)
        discoveries = await navigation.discovered_ids(character_id)

        character_payload: dict[str, JsonValue] = {
            "id": str(character.id),
            "race_id": str(character.race_id),
            "active_job_id": str(character.active_job_id),
            "current_location_id": str(character.current_location_id),
            "name": character.name,
            "gender": character.gender,
            "alignment": character.alignment,
            "level": character.level,
            "experience": character.experience,
            "skill_points": character.skill_points,
            "strength": character.strength,
            "dexterity": character.dexterity,
            "agility": character.agility,
            "vitality": character.vitality,
            "intelligence": character.intelligence,
            "wisdom": character.wisdom,
            "charisma": character.charisma,
            "current_hp": character.current_hp,
            "current_mp": character.current_mp,
            "current_stamina": character.current_stamina,
            "gold": character.gold,
            "fame": character.fame,
            "karma": character.karma,
            "jobs": [
                {
                    "id": str(character_job.id),
                    "job_id": str(job.id),
                    "job_level": character_job.job_level,
                    "experience": character_job.experience,
                }
                for character_job, job in jobs
            ],
            "skills": [
                {
                    "id": str(character_skill.id),
                    "skill_id": str(skill.id),
                    "skill_level": character_skill.skill_level,
                }
                for character_skill, skill in skills
            ],
        }
        inventory_payload: dict[str, JsonValue] = (
            {
                "id": str(inventory.id),
                "slot_count": inventory.slot_count,
                "max_weight": float(inventory.max_weight),
                "items": [
                    {
                        "id": str(entry.id),
                        "item_id": str(item.id),
                        "quantity": entry.quantity,
                        "slot_index": entry.slot_index,
                        "unique_instance_id": (
                            str(entry.unique_instance_id)
                            if entry.unique_instance_id
                            else None
                        ),
                    }
                    for entry, item in entries
                ],
            }
            if inventory is not None
            else {}
        )
        equipment_payload: dict[str, JsonValue] = {
            "items": [
                {
                    "id": str(row.id),
                    "slot_id": str(slot.id),
                    "inventory_item_id": str(entry.id),
                }
                for row, slot, entry, _ in equipped
            ]
        }
        discovered_values: list[JsonValue] = [
            str(value) for value in sorted(discoveries, key=str)
        ]
        world_payload: dict[str, JsonValue] = {
            "current_location_id": str(character.current_location_id),
            "discovered_location_ids": discovered_values,
        }
        world = await WorldRepository(self._session).capture(player_id, character_id)
        return CanonicalSnapshot(
            character=character_payload,
            inventory=inventory_payload,
            equipment=equipment_payload,
            world_state=world_payload,
            quest_state=world.quest_state,
            npc_state=world.npc_state,
            faction_state=world.faction_state,
            relationships=world.relationships,
            journal=world.journal,
            memories=world.memories,
            dungeon_state=world.dungeon_state,
        )

    async def restore(
        self,
        player_id: UUID,
        character_id: UUID,
        snapshot: CanonicalSnapshot,
    ) -> bool:
        character = await CharacterRepository(self._session).get_owned(
            player_id, character_id, for_update=True
        )
        payload = snapshot.character
        if character is None or payload.get("id") != str(character_id):
            return False

        scalar_fields = (
            "race_id",
            "active_job_id",
            "current_location_id",
            "name",
            "gender",
            "alignment",
            "level",
            "experience",
            "skill_points",
            "strength",
            "dexterity",
            "agility",
            "vitality",
            "intelligence",
            "wisdom",
            "charisma",
            "current_hp",
            "current_mp",
            "current_stamina",
            "gold",
            "fame",
            "karma",
        )
        uuid_fields = {"race_id", "active_job_id", "current_location_id"}
        for field_name in scalar_fields:
            value = payload[field_name]
            setattr(
                character,
                field_name,
                UUID(str(value)) if field_name in uuid_fields else value,
            )

        await self._session.execute(
            delete(EquippedItem).where(EquippedItem.character_id == character_id)
        )
        inventory = await InventoryRepository(self._session).get_for_character(
            character_id, for_update=True
        )
        if inventory is not None:
            await self._session.execute(
                delete(InventoryItem).where(InventoryItem.inventory_id == inventory.id)
            )
        await self._session.execute(
            delete(CharacterSkill).where(CharacterSkill.character_id == character_id)
        )
        await self._session.execute(
            delete(CharacterJob).where(CharacterJob.character_id == character_id)
        )
        await self._session.execute(
            delete(CharacterLocationDiscovery).where(
                CharacterLocationDiscovery.character_id == character_id
            )
        )
        await self._session.flush()

        jobs = payload.get("jobs", [])
        if not isinstance(jobs, list):
            raise ValueError("Saved character jobs must be a list")
        for row in jobs:
            if not isinstance(row, dict):
                raise ValueError("Saved character job must be an object")
            self._session.add(
                CharacterJob(
                    id=UUID(str(row["id"])),
                    player_id=player_id,
                    character_id=character_id,
                    job_id=UUID(str(row["job_id"])),
                    job_level=_json_int(row["job_level"]),
                    experience=_json_int(row["experience"]),
                )
            )
        skills = payload.get("skills", [])
        if not isinstance(skills, list):
            raise ValueError("Saved character skills must be a list")
        for row in skills:
            if not isinstance(row, dict):
                raise ValueError("Saved character skill must be an object")
            self._session.add(
                CharacterSkill(
                    id=UUID(str(row["id"])),
                    character_id=character_id,
                    skill_id=UUID(str(row["skill_id"])),
                    skill_level=_json_int(row["skill_level"]),
                )
            )

        inventory_payload = snapshot.inventory
        if inventory_payload:
            if inventory is None:
                inventory = Inventory(
                    id=UUID(str(inventory_payload["id"])),
                    character_id=character_id,
                    slot_count=_json_int(inventory_payload["slot_count"]),
                    max_weight=_json_float(inventory_payload["max_weight"]),
                )
                self._session.add(inventory)
            else:
                inventory.slot_count = _json_int(inventory_payload["slot_count"])
                inventory.max_weight = _json_float(inventory_payload["max_weight"])
            await self._session.flush()
            saved_items = inventory_payload.get("items", [])
            if not isinstance(saved_items, list):
                raise ValueError("Saved inventory items must be a list")
            for row in saved_items:
                if not isinstance(row, dict):
                    raise ValueError("Saved inventory item must be an object")
                instance = row.get("unique_instance_id")
                self._session.add(
                    InventoryItem(
                        id=UUID(str(row["id"])),
                        inventory_id=inventory.id,
                        item_id=UUID(str(row["item_id"])),
                        quantity=_json_int(row["quantity"]),
                        slot_index=_json_int(row["slot_index"]),
                        unique_instance_id=UUID(str(instance)) if instance else None,
                    )
                )
        await self._session.flush()

        equipment = snapshot.equipment.get("items", [])
        if not isinstance(equipment, list):
            raise ValueError("Saved equipment items must be a list")
        for row in equipment:
            if not isinstance(row, dict):
                raise ValueError("Saved equipment item must be an object")
            self._session.add(
                EquippedItem(
                    id=UUID(str(row["id"])),
                    character_id=character_id,
                    slot_id=UUID(str(row["slot_id"])),
                    inventory_item_id=UUID(str(row["inventory_item_id"])),
                )
            )

        discovered = snapshot.world_state.get("discovered_location_ids", [])
        if not isinstance(discovered, list):
            raise ValueError("Saved discoveries must be a list")
        for location_id in discovered:
            self._session.add(
                CharacterLocationDiscovery(
                    character_id=character_id,
                    location_id=UUID(str(location_id)),
                )
            )
        await WorldRepository(self._session).restore(
            player_id,
            character_id,
            WorldSnapshot(
                quest_state=snapshot.quest_state,
                npc_state=snapshot.npc_state,
                faction_state=snapshot.faction_state,
                relationships=snapshot.relationships,
                journal=snapshot.journal,
                memories=snapshot.memories,
                dungeon_state=snapshot.dungeon_state,
            ),
        )
        await self._session.flush()
        return True


class GameUnitOfWork:
    """Own one transaction spanning all v0.5 gameplay repositories."""

    def __init__(self, session: AsyncSession) -> None:
        self.definitions = DefinitionRepository(session)
        self.characters = CharacterRepository(session)
        self.inventory = InventoryRepository(session)
        self.equipment = EquipmentRepository(session)
        self.navigation = NavigationRepository(session)
        self.idempotency = IdempotencyRepository(session)
        self.game_state = GameStateRepository(session)
        self._session = session
        self._transaction: AsyncSessionTransaction | None = None

    async def __aenter__(self) -> "GameUnitOfWork":
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        return self

    async def lock_key(self, value: str) -> None:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:value, 0))"),
            {"value": value},
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._transaction is None:
            raise RuntimeError("GameUnitOfWork exited before it was entered")
        await self._transaction.__aexit__(exc_type, exc_value, traceback)
