from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, EntityMixin


class Race(EntityMixin, Base):
    """Engine-owned playable race definition."""

    __tablename__ = "races"

    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    lore: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    selectable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    base_stats: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False)
    racial_bonuses: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False)
    racial_penalties: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False)
    racial_passives: Mapped[list[str]] = mapped_column(JSONB, nullable=False)


class Job(EntityMixin, Base):
    """Versionable job definition with data-driven prerequisite expressions."""

    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(
            "tier IN ('BASIC', 'HIGH', 'RARE', 'WORLD')",
            name="ck_jobs_tier",
        ),
        CheckConstraint("max_level BETWEEN 1 AND 15", name="ck_jobs_max_level"),
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    lore: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    max_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    selectable_at_creation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    prerequisites: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    skill_unlocks: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False
    )
    passive_unlocks: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False
    )
    stat_modifiers: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False)


class Skill(EntityMixin, Base):
    """Engine-owned skill definition; effects are structured, never AI-authored."""

    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint("mana_cost >= 0", name="ck_skills_mana_cost"),
        CheckConstraint("cooldown >= 0", name="ck_skills_cooldown"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skill_type: Mapped[str] = mapped_column(String(30), nullable=False)
    mana_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cooldown: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    effect_definitions: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False
    )


class JobSkill(EntityMixin, Base):
    """Level-gated skill unlock owned by one job definition."""

    __tablename__ = "job_skills"
    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),
        CheckConstraint("required_level >= 1", name="ck_job_skills_required_level"),
    )

    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    required_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class Location(EntityMixin, Base):
    """Canonical location definition used by deterministic navigation."""

    __tablename__ = "locations"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    location_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    danger_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_starting_location: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )


class LocationRoute(EntityMixin, Base):
    """Directed, data-driven edge in the world navigation graph."""

    __tablename__ = "location_routes"
    __table_args__ = (
        UniqueConstraint(
            "origin_location_id",
            "destination_location_id",
            name="uq_location_routes_edge",
        ),
        CheckConstraint(
            "origin_location_id <> destination_location_id",
            name="ck_location_routes_distinct",
        ),
        CheckConstraint("travel_cost >= 0", name="ck_location_routes_cost"),
    )

    origin_location_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    destination_location_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    travel_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    requirements: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)


class Character(EntityMixin, Base):
    """Canonical player-owned character state."""

    __tablename__ = "characters"
    __table_args__ = (
        UniqueConstraint("player_id", "name", name="uq_characters_player_name"),
        CheckConstraint("level BETWEEN 1 AND 100", name="ck_characters_level"),
        CheckConstraint("experience >= 0", name="ck_characters_experience"),
        CheckConstraint("karma BETWEEN -500 AND 500", name="ck_characters_karma"),
        CheckConstraint(
            "current_hp >= 0 AND current_mp >= 0 AND current_stamina >= 0",
            name="ck_characters_resources",
        ),
    )

    player_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    race_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("races.id"), nullable=False, index=True
    )
    active_job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    current_location_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id"), nullable=False, index=True
    )
    gender: Mapped[str] = mapped_column(String(30), nullable=False)
    alignment: Mapped[str] = mapped_column(String(30), nullable=False)
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skill_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strength: Mapped[int] = mapped_column(Integer, nullable=False)
    dexterity: Mapped[int] = mapped_column(Integer, nullable=False)
    agility: Mapped[int] = mapped_column(Integer, nullable=False)
    vitality: Mapped[int] = mapped_column(Integer, nullable=False)
    intelligence: Mapped[int] = mapped_column(Integer, nullable=False)
    wisdom: Mapped[int] = mapped_column(Integer, nullable=False)
    charisma: Mapped[int] = mapped_column(Integer, nullable=False)
    current_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    current_mp: Mapped[int] = mapped_column(Integer, nullable=False)
    current_stamina: Mapped[int] = mapped_column(Integer, nullable=False)
    gold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fame: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    karma: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CharacterJob(EntityMixin, Base):
    """One character's deterministic progress in one job."""

    __tablename__ = "character_jobs"
    __table_args__ = (
        UniqueConstraint("character_id", "job_id", name="uq_character_jobs"),
        CheckConstraint("job_level >= 1", name="ck_character_jobs_level"),
        CheckConstraint("experience >= 0", name="ck_character_jobs_experience"),
    )

    player_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    character_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    job_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CharacterSkill(EntityMixin, Base):
    """A skill deterministically unlocked by progression."""

    __tablename__ = "character_skills"
    __table_args__ = (
        UniqueConstraint(
            "character_id", "skill_id", name="uq_character_skills_character_skill"
        ),
        CheckConstraint("skill_level >= 1", name="ck_character_skills_level"),
    )

    character_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("skills.id"), nullable=False, index=True
    )
    skill_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)


class Item(EntityMixin, Base):
    """Engine-owned item definition with narrative-only lore."""

    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("weight >= 0", name="ck_items_weight"),
        CheckConstraint("base_value >= 0", name="ck_items_value"),
        CheckConstraint("max_stack >= 1", name="ck_items_max_stack"),
        CheckConstraint("required_level >= 1", name="ck_items_required_level"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    lore: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)
    rarity: Mapped[str] = mapped_column(String(20), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    base_value: Mapped[int] = mapped_column(Integer, nullable=False)
    base_stats: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False)
    compatible_slots: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    is_stackable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    max_stack: Mapped[int] = mapped_column(Integer, nullable=False)
    is_quest_item: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_droppable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    required_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Inventory(EntityMixin, Base):
    """One atomic inventory container per character."""

    __tablename__ = "inventories"
    __table_args__ = (
        UniqueConstraint("character_id", name="uq_inventories_character"),
        CheckConstraint("slot_count > 0", name="ck_inventories_slots"),
        CheckConstraint("max_weight > 0", name="ck_inventories_weight"),
    )

    character_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot_count: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    max_weight: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class InventoryItem(EntityMixin, Base):
    """Stack or unique item instance held by an inventory."""

    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("inventory_id", "slot_index", name="uq_inventory_items_slot"),
        CheckConstraint("quantity > 0", name="ck_inventory_items_quantity"),
        CheckConstraint("slot_index >= 0", name="ck_inventory_items_slot"),
        Index(
            "uq_inventory_items_unique_instance",
            "unique_instance_id",
            unique=True,
            postgresql_where=text("unique_instance_id IS NOT NULL"),
        ),
    )

    inventory_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("inventories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("items.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_index: Mapped[int] = mapped_column(Integer, nullable=False)
    unique_instance_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )


class EquipmentSlot(EntityMixin, Base):
    """Named equipment slot definition."""

    __tablename__ = "equipment_slots"

    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)


class EquippedItem(EntityMixin, Base):
    """One inventory item equipped in one character slot."""

    __tablename__ = "equipped_items"
    __table_args__ = (
        UniqueConstraint("character_id", "slot_id", name="uq_equipped_items_slot"),
        UniqueConstraint("inventory_item_id", name="uq_equipped_items_inventory_item"),
    )

    character_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("equipment_slots.id"),
        nullable=False,
        index=True,
    )
    inventory_item_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
    )


class CharacterLocationDiscovery(EntityMixin, Base):
    """Per-character permanent location discovery state."""

    __tablename__ = "character_location_discoveries"
    __table_args__ = (
        UniqueConstraint(
            "character_id",
            "location_id",
            name="uq_character_location_discoveries",
        ),
    )

    character_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=False,
        index=True,
    )
