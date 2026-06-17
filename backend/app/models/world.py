from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, EntityMixin


class Faction(EntityMixin, Base):
    """Canonical faction definition."""

    __tablename__ = "factions"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class CharacterFaction(EntityMixin, Base):
    """Persistent character standing with one faction."""

    __tablename__ = "character_factions"
    __table_args__ = (
        UniqueConstraint("character_id", "faction_id", name="uq_character_factions"),
        CheckConstraint(
            "reputation BETWEEN -1000 AND 1000",
            name="ck_character_factions_reputation",
        ),
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
    faction_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("factions.id"), nullable=False, index=True
    )
    reputation: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rank: Mapped[str] = mapped_column(String(40), nullable=False, default="OUTSIDER")
    joined: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Dungeon(EntityMixin, Base):
    """Persistent dungeon definition."""

    __tablename__ = "dungeons"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id"), nullable=False, index=True
    )
    recommended_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class CharacterDungeonState(EntityMixin, Base):
    """Permanent per-character dungeon and boss state."""

    __tablename__ = "character_dungeon_states"
    __table_args__ = (
        UniqueConstraint("character_id", "dungeon_id", name="uq_character_dungeons"),
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
    dungeon_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("dungeons.id"), nullable=False, index=True
    )
    entered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cleared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    boss_alive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NPC(EntityMixin, Base):
    """Deterministic NPC profile, knowledge, and daily schedule."""

    __tablename__ = "npcs"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    race_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("races.id"), nullable=False
    )
    faction_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("factions.id")
    )
    home_location_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id"), nullable=False
    )
    occupation: Mapped[str] = mapped_column(String(80), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    personality_profile: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False
    )
    schedule: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    knowledge: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    is_alive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Relationship(EntityMixin, Base):
    """Numeric, engine-owned relationship between one character and NPC."""

    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint("character_id", "npc_id", name="uq_relationships"),
        CheckConstraint(
            "trust BETWEEN -100 AND 100 AND friendship BETWEEN -100 AND 100 "
            "AND respect BETWEEN -100 AND 100 AND fear BETWEEN -100 AND 100 "
            "AND hatred BETWEEN -100 AND 100 AND loyalty BETWEEN -100 AND 100",
            name="ck_relationship_values",
        ),
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
    npc_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("npcs.id"), nullable=False, index=True
    )
    trust: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    friendship: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    respect: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    fear: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    hatred: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    loyalty: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Quest(EntityMixin, Base):
    """Engine-owned quest definition."""

    __tablename__ = "quests"

    title: Mapped[str] = mapped_column(String(140), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id"), nullable=False, index=True
    )
    giver_npc_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("npcs.id")
    )
    faction_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("factions.id")
    )
    minimum_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    prerequisites: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    rewards: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    repeatable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class QuestStep(EntityMixin, Base):
    """Ordered deterministic quest objective."""

    __tablename__ = "quest_steps"
    __table_args__ = (
        UniqueConstraint("quest_id", "sequence", name="uq_quest_steps_sequence"),
        CheckConstraint("sequence >= 0", name="ck_quest_steps_sequence"),
        CheckConstraint("required_count > 0", name="ck_quest_steps_required"),
    )

    quest_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    objective_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class CharacterQuest(EntityMixin, Base):
    """Canonical per-character quest state."""

    __tablename__ = "character_quests"
    __table_args__ = (
        UniqueConstraint("character_id", "quest_id", name="uq_character_quests"),
        CheckConstraint(
            "status IN ('NOT_STARTED', 'ACTIVE', 'COMPLETED', 'FAILED', 'ARCHIVED')",
            name="ck_character_quests_status",
        ),
        CheckConstraint(
            "current_step >= 0 AND step_progress >= 0", name="ck_quest_progress"
        ),
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
    quest_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("quests.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="NOT_STARTED"
    )
    current_step: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    step_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    objectives_complete: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    rewards_claimed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JournalEntry(EntityMixin, Base):
    """Permanent engine-authored quest and world journal entry."""

    __tablename__ = "journal_entries"

    player_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    character_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quest_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("quests.id")
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class WorldEvent(EntityMixin, Base):
    """Immutable significant world outcome."""

    __tablename__ = "world_events"
    __table_args__ = (
        UniqueConstraint("deduplication_key", name="uq_world_events_deduplication"),
    )

    player_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    character_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("characters.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    location_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id")
    )
    faction_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("factions.id")
    )
    quest_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("quests.id")
    )
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    deduplication_key: Mapped[str] = mapped_column(String(180), nullable=False)
