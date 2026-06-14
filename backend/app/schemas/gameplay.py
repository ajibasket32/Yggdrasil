from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RaceView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    lore: str
    category: str
    base_stats: dict[str, int]
    racial_bonuses: dict[str, int]
    racial_penalties: dict[str, int]
    racial_passives: list[str]


class JobView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    lore: str
    tier: str
    max_level: int
    selectable_at_creation: bool
    prerequisites: dict[str, object]
    skill_unlocks: list[dict[str, object]]
    passive_unlocks: list[dict[str, object]]
    stat_modifiers: dict[str, int]


class SkillView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    skill_type: str
    mana_cost: int
    cooldown: int
    target_type: str
    effect_definitions: list[dict[str, object]]
    skill_level: int = 1


class LocationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    location_type: str
    description: str
    danger_level: int
    discovered: bool = False
    reachable: bool = False


class CharacterCreationDefinitions(BaseModel):
    races: list[RaceView]
    starting_jobs: list[JobView]
    starting_location: LocationView


class CreateCharacterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z][A-Za-z '\-]*$")
    race_id: UUID
    gender: str = Field(min_length=1, max_length=30)
    alignment: Literal["GOOD", "NEUTRAL", "EVIL"]
    starting_job_id: UUID

    @field_validator("name", "gender", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if isinstance(value, str):
            return " ".join(value.split())
        return value


class StatBlock(BaseModel):
    strength: int
    dexterity: int
    agility: int
    vitality: int
    intelligence: int
    wisdom: int
    charisma: int


class DerivedStatBlock(BaseModel):
    max_hp: int
    max_mp: int
    max_stamina: int
    physical_attack: int
    physical_defense: int
    magic_attack: int
    magic_defense: int
    accuracy: int
    evasion: int
    critical_chance: float
    initiative: int


class JobProgressView(BaseModel):
    job: JobView
    job_level: int
    experience: int
    experience_to_next: int
    active: bool


class CharacterSummary(BaseModel):
    id: UUID
    name: str
    race: RaceView
    level: int
    current_job: JobView
    current_location: LocationView
    created_at: datetime


class CharacterSheet(CharacterSummary):
    gender: str = Field(min_length=1, max_length=30)
    alignment: str = Field(pattern=r"^(GOOD|NEUTRAL|EVIL)$")
    experience: int = Field(ge=0)
    experience_to_next: int = Field(ge=0)
    skill_points: int = Field(ge=0)
    stats: StatBlock
    derived_stats: DerivedStatBlock
    current_hp: int = Field(ge=0)
    current_mp: int = Field(ge=0)
    current_stamina: int = Field(ge=0)
    gold: int = Field(ge=0)
    fame: int = Field(ge=0)
    karma: int = Field(ge=-10000, le=10000)
    jobs: list[JobProgressView]
    skills: list[SkillView]


class AwardExperienceRequest(BaseModel):
    amount: int = Field(gt=0, le=1_000_000)


class JobMutationRequest(BaseModel):
    job_id: UUID


class InventoryItemView(BaseModel):
    inventory_item_id: UUID
    item_id: UUID
    name: str = Field(min_length=1, max_length=100)
    item_type: str = Field(min_length=1, max_length=50)
    rarity: str = Field(min_length=1, max_length=20)
    weight: float = Field(ge=0.0)
    value: int = Field(ge=0)
    quantity: int = Field(ge=1)
    slot_index: int = Field(ge=0)
    is_quest_item: bool
    is_droppable: bool
    is_equipped: bool


class InventoryView(BaseModel):
    inventory_id: UUID
    slot_count: int
    used_slots: int
    total_weight: float
    max_weight: float
    items: list[InventoryItemView]


class DropItemRequest(BaseModel):
    character_id: UUID
    inventory_item_id: UUID
    quantity: int = Field(gt=0)


class SplitStackRequest(BaseModel):
    character_id: UUID
    inventory_item_id: UUID
    quantity: int = Field(gt=0)


class MergeStackRequest(BaseModel):
    character_id: UUID
    source_inventory_item_id: UUID
    target_inventory_item_id: UUID


class SortInventoryRequest(BaseModel):
    character_id: UUID


class EquipItemRequest(BaseModel):
    character_id: UUID
    inventory_item_id: UUID
    slot_id: UUID


class UnequipItemRequest(BaseModel):
    character_id: UUID
    slot_id: UUID


class EquipmentItemView(BaseModel):
    inventory_item_id: UUID
    item_id: UUID
    name: str
    base_stats: dict[str, int]


class EquipmentSlotView(BaseModel):
    slot_id: UUID
    code: str
    name: str
    item: EquipmentItemView | None


class EquipmentView(BaseModel):
    slots: list[EquipmentSlotView]
    total_equipment_bonuses: dict[str, int]


class TravelRequest(BaseModel):
    destination_id: UUID


class TravelResult(BaseModel):
    character_id: UUID
    origin: LocationView
    destination: LocationView
    newly_discovered: bool
