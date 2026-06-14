"""Create deterministic combat definitions and canonical encounter state.

Revision ID: 0004_combat_system
Revises: 0003_character_system
Create Date: 2026-06-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_combat_system"
down_revision: str | None = "0003_character_system"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

POTION_ID = "54000000-0000-0000-0000-000000000001"
GREENWOOD_ID = "56000000-0000-0000-0000-000000000002"
CROSSROADS_ID = "56000000-0000-0000-0000-000000000004"
SLIME_ID = "70000000-0000-0000-0000-000000000001"
CRAWLER_ID = "70000000-0000-0000-0000-000000000002"
SLIME_ENCOUNTER_ID = "71000000-0000-0000-0000-000000000001"
CRAWLER_ENCOUNTER_ID = "71000000-0000-0000-0000-000000000002"


def _audit_columns() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    ]


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    """Create and seed the complete v0.6 canonical combat foundation."""
    op.create_table(
        "monsters",
        *_audit_columns(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("level", sa.SmallInteger(), nullable=False),
        sa.Column("family", sa.String(40), nullable=False),
        sa.Column("max_hp", sa.Integer(), nullable=False),
        sa.Column("max_mp", sa.Integer(), nullable=False),
        sa.Column("max_stamina", sa.Integer(), nullable=False),
        sa.Column("combat_stats", _json(), nullable=False),
        sa.Column("resistances", _json(), nullable=False),
        sa.Column("behavior", _json(), nullable=False),
        sa.Column("reward_experience", sa.Integer(), nullable=False),
        sa.Column("reward_gold", sa.Integer(), nullable=False),
        sa.Column("loot_item_id", sa.Uuid(), sa.ForeignKey("items.id"), nullable=True),
        sa.Column("loot_chance_percent", sa.Integer(), nullable=False),
        sa.Column(
            "escape_blocked", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.CheckConstraint("level >= 1", name="ck_monsters_level"),
        sa.CheckConstraint(
            "max_hp > 0 AND max_mp >= 0 AND max_stamina >= 0",
            name="ck_monsters_resources",
        ),
        sa.CheckConstraint(
            "reward_experience >= 0 AND reward_gold >= 0",
            name="ck_monsters_rewards",
        ),
        sa.CheckConstraint(
            "loot_chance_percent BETWEEN 0 AND 100",
            name="ck_monsters_loot_chance",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_monsters_name"),
    )
    op.create_table(
        "encounter_definitions",
        *_audit_columns(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column(
            "location_id",
            sa.Uuid(),
            sa.ForeignKey("locations.id"),
            nullable=False,
        ),
        sa.Column(
            "monster_id",
            sa.Uuid(),
            sa.ForeignKey("monsters.id"),
            nullable=False,
        ),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_encounter_definitions_name"),
    )
    op.create_index(
        "ix_encounter_definitions_location_id",
        "encounter_definitions",
        ["location_id"],
    )
    op.create_index(
        "ix_encounter_definitions_monster_id",
        "encounter_definitions",
        ["monster_id"],
    )
    op.create_table(
        "combat_encounters",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "encounter_definition_id",
            sa.Uuid(),
            sa.ForeignKey("encounter_definitions.id"),
            nullable=False,
        ),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column("round_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("action_sequence", sa.Integer(), server_default="0", nullable=False),
        sa.Column("turn_order", _json(), nullable=False),
        sa.Column("rewards", _json(), nullable=False),
        sa.Column(
            "rewards_applied", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'VICTORY', 'DEFEAT', 'FLED')",
            name="ck_combat_encounters_status",
        ),
        sa.CheckConstraint("round_number >= 1", name="ck_combat_encounters_round"),
        sa.CheckConstraint(
            "action_sequence >= 0", name="ck_combat_encounters_sequence"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_combat_encounters_player_id", "combat_encounters", ["player_id"]
    )
    op.create_index(
        "ix_combat_encounters_character_id", "combat_encounters", ["character_id"]
    )
    op.create_index(
        "ix_combat_encounters_active_character",
        "combat_encounters",
        ["character_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )
    op.create_table(
        "combat_participants",
        *_audit_columns(),
        sa.Column(
            "encounter_id",
            sa.Uuid(),
            sa.ForeignKey("combat_encounters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("level", sa.SmallInteger(), nullable=False),
        sa.Column("current_hp", sa.Integer(), nullable=False),
        sa.Column("max_hp", sa.Integer(), nullable=False),
        sa.Column("current_mp", sa.Integer(), nullable=False),
        sa.Column("max_mp", sa.Integer(), nullable=False),
        sa.Column("current_stamina", sa.Integer(), nullable=False),
        sa.Column("max_stamina", sa.Integer(), nullable=False),
        sa.Column("combat_stats", _json(), nullable=False),
        sa.Column("statuses", _json(), nullable=False),
        sa.Column("guarding", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint(
            "side IN ('PLAYER', 'ENEMY')", name="ck_combat_participant_side"
        ),
        sa.CheckConstraint(
            "current_hp >= 0 AND current_mp >= 0 AND current_stamina >= 0",
            name="ck_combat_participant_resources",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "encounter_id",
            "source_type",
            "source_id",
            name="uq_combat_participant",
        ),
    )
    op.create_index(
        "ix_combat_participants_encounter_id",
        "combat_participants",
        ["encounter_id"],
    )
    op.create_table(
        "combat_log_entries",
        *_audit_columns(),
        sa.Column(
            "encounter_id",
            sa.Uuid(),
            sa.ForeignKey("combat_encounters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column(
            "actor_participant_id",
            sa.Uuid(),
            sa.ForeignKey("combat_participants.id"),
            nullable=True,
        ),
        sa.Column(
            "target_participant_id",
            sa.Uuid(),
            sa.ForeignKey("combat_participants.id"),
            nullable=True,
        ),
        sa.Column("action_type", sa.String(20), nullable=False),
        sa.Column("outcome", _json(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("encounter_id", "sequence", name="uq_combat_log_sequence"),
    )
    op.create_index(
        "ix_combat_log_entries_encounter_id",
        "combat_log_entries",
        ["encounter_id"],
    )
    op.create_table(
        "game_outbox_events",
        *_audit_columns(),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("aggregate_type", sa.String(40), nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("deduplication_key", sa.String(160), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deduplication_key", name="uq_game_outbox_deduplication"),
    )
    op.create_index(
        "ix_game_outbox_events_event_type", "game_outbox_events", ["event_type"]
    )

    monsters = sa.table(
        "monsters",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("level", sa.SmallInteger()),
        sa.column("family", sa.String()),
        sa.column("max_hp", sa.Integer()),
        sa.column("max_mp", sa.Integer()),
        sa.column("max_stamina", sa.Integer()),
        sa.column("combat_stats", _json()),
        sa.column("resistances", _json()),
        sa.column("behavior", _json()),
        sa.column("reward_experience", sa.Integer()),
        sa.column("reward_gold", sa.Integer()),
        sa.column("loot_item_id", sa.Uuid()),
        sa.column("loot_chance_percent", sa.Integer()),
        sa.column("escape_blocked", sa.Boolean()),
    )
    op.bulk_insert(
        monsters,
        [
            {
                "id": SLIME_ID,
                "name": "Greenwood Slime",
                "level": 1,
                "family": "SLIME",
                "max_hp": 55,
                "max_mp": 0,
                "max_stamina": 40,
                "combat_stats": {
                    "physical_attack": 17,
                    "physical_defense": 6,
                    "magic_attack": 8,
                    "magic_defense": 5,
                    "accuracy": 68,
                    "evasion": 6,
                    "critical_chance": 2,
                    "initiative": 8,
                },
                "resistances": {},
                "behavior": {},
                "reward_experience": 45,
                "reward_gold": 18,
                "loot_item_id": POTION_ID,
                "loot_chance_percent": 50,
                "escape_blocked": False,
            },
            {
                "id": CRAWLER_ID,
                "name": "Ash Crawler",
                "level": 2,
                "family": "BEAST",
                "max_hp": 85,
                "max_mp": 12,
                "max_stamina": 50,
                "combat_stats": {
                    "physical_attack": 22,
                    "physical_defense": 9,
                    "magic_attack": 18,
                    "magic_defense": 8,
                    "accuracy": 72,
                    "evasion": 8,
                    "critical_chance": 4,
                    "initiative": 12,
                },
                "resistances": {"fire": 25},
                "behavior": {"skill": "EMBER_BITE"},
                "reward_experience": 75,
                "reward_gold": 30,
                "loot_item_id": POTION_ID,
                "loot_chance_percent": 65,
                "escape_blocked": False,
            },
        ],
    )
    encounters = sa.table(
        "encounter_definitions",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("location_id", sa.Uuid()),
        sa.column("monster_id", sa.Uuid()),
        sa.column("difficulty", sa.String()),
        sa.column("enabled", sa.Boolean()),
    )
    op.bulk_insert(
        encounters,
        [
            {
                "id": SLIME_ENCOUNTER_ID,
                "name": "Slime on the Verge",
                "location_id": GREENWOOD_ID,
                "monster_id": SLIME_ID,
                "difficulty": "NORMAL",
                "enabled": True,
            },
            {
                "id": CRAWLER_ENCOUNTER_ID,
                "name": "Crawler at the Crossroads",
                "location_id": CROSSROADS_ID,
                "monster_id": CRAWLER_ID,
                "difficulty": "NORMAL",
                "enabled": True,
            },
        ],
    )
    for table in (
        "monsters",
        "encounter_definitions",
        "combat_encounters",
        "combat_participants",
        "combat_log_entries",
        "game_outbox_events",
    ):
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """)


def downgrade() -> None:
    """Remove v0.6 combat state without changing prior releases."""
    for table in (
        "game_outbox_events",
        "combat_log_entries",
        "combat_participants",
        "combat_encounters",
        "encounter_definitions",
        "monsters",
    ):
        op.drop_table(table)
