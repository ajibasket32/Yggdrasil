from datetime import UTC, datetime
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


class Monster(EntityMixin, Base):
    """Engine-owned enemy definition."""

    __tablename__ = "monsters"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    family: Mapped[str] = mapped_column(String(40), nullable=False)
    max_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    max_mp: Mapped[int] = mapped_column(Integer, nullable=False)
    max_stamina: Mapped[int] = mapped_column(Integer, nullable=False)
    combat_stats: Mapped[dict[str, int | float]] = mapped_column(JSONB, nullable=False)
    resistances: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False)
    behavior: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    reward_experience: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_gold: Mapped[int] = mapped_column(Integer, nullable=False)
    loot_item_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("items.id"), nullable=True
    )
    loot_chance_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    escape_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class EncounterDefinition(EntityMixin, Base):
    """Location-bound deterministic encounter definition."""

    __tablename__ = "encounter_definitions"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    location_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id"), nullable=False, index=True
    )
    monster_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("monsters.id"), nullable=False, index=True
    )
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CombatEncounter(EntityMixin, Base):
    """Canonical state of one player-owned encounter."""

    __tablename__ = "combat_encounters"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'VICTORY', 'DEFEAT', 'FLED')",
            name="ck_combat_encounters_status",
        ),
        CheckConstraint("round_number >= 1", name="ck_combat_encounters_round"),
        CheckConstraint("action_sequence >= 0", name="ck_combat_encounters_sequence"),
    )

    player_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    character_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    encounter_definition_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("encounter_definitions.id"), nullable=False
    )
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    action_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    turn_order: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    rewards: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    rewards_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CombatParticipant(EntityMixin, Base):
    """Snapshot and mutable resources for one combatant."""

    __tablename__ = "combat_participants"
    __table_args__ = (
        UniqueConstraint("encounter_id", "source_type", "source_id", name="uq_combat_participant"),
        CheckConstraint("side IN ('PLAYER', 'ENEMY')", name="ck_combat_participant_side"),
        CheckConstraint(
            "current_hp >= 0 AND current_mp >= 0 AND current_stamina >= 0",
            name="ck_combat_participant_resources",
        ),
    )

    encounter_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("combat_encounters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    current_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    max_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    current_mp: Mapped[int] = mapped_column(Integer, nullable=False)
    max_mp: Mapped[int] = mapped_column(Integer, nullable=False)
    current_stamina: Mapped[int] = mapped_column(Integer, nullable=False)
    max_stamina: Mapped[int] = mapped_column(Integer, nullable=False)
    combat_stats: Mapped[dict[str, int | float]] = mapped_column(JSONB, nullable=False)
    statuses: Mapped[list[dict[str, int | str]]] = mapped_column(JSONB, nullable=False)
    guarding: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CombatLogEntry(EntityMixin, Base):
    """Immutable ordered combat record."""

    __tablename__ = "combat_log_entries"
    __table_args__ = (UniqueConstraint("encounter_id", "sequence", name="uq_combat_log_sequence"),)

    encounter_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("combat_encounters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_participant_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("combat_participants.id"), nullable=True
    )
    target_participant_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("combat_participants.id"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    outcome: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)


class GameOutboxEvent(EntityMixin, Base):
    """Immutable post-commit event ready for at-least-once publication."""

    __tablename__ = "outbox_events"
    __table_args__ = (UniqueConstraint("deduplication_key", name="uq_outbox_deduplication"),)

    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(40), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    player_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    deduplication_key: Mapped[str] = mapped_column(String(160), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
