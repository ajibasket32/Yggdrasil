"""Create deterministic world, NPC, relationship, dungeon, and quest state.

Revision ID: 0006_world_npc_quest
Revises: 0005_combat_outbox_contract
Create Date: 2026-06-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_world_npc_quest"
down_revision: str | None = "0005_combat_outbox_contract"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

HUMAN_ID = "51000000-0000-0000-0000-000000000001"
GREENWOOD_ID = "56000000-0000-0000-0000-000000000002"
CROSSROADS_ID = "56000000-0000-0000-0000-000000000004"
FACTION_ID = "72000000-0000-0000-0000-000000000001"
DUNGEON_ID = "73000000-0000-0000-0000-000000000001"
NPC_ID = "74000000-0000-0000-0000-000000000001"
QUEST_ID = "75000000-0000-0000-0000-000000000001"


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


def _create_world_tables() -> None:
    op.create_table(
        "factions",
        *_audit_columns(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_factions_name"),
    )
    op.create_table(
        "dungeons",
        *_audit_columns(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location_id", sa.Uuid(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("recommended_level", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("recommended_level >= 1", name="ck_dungeons_level"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_dungeons_name"),
    )
    op.create_index("ix_dungeons_location_id", "dungeons", ["location_id"])
    op.create_table(
        "npcs",
        *_audit_columns(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("race_id", sa.Uuid(), sa.ForeignKey("races.id"), nullable=False),
        sa.Column("faction_id", sa.Uuid(), sa.ForeignKey("factions.id"), nullable=True),
        sa.Column(
            "home_location_id",
            sa.Uuid(),
            sa.ForeignKey("locations.id"),
            nullable=False,
        ),
        sa.Column("occupation", sa.String(80), nullable=False),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("personality_profile", _json(), nullable=False),
        sa.Column("schedule", _json(), nullable=False),
        sa.Column("knowledge", _json(), nullable=False),
        sa.Column("is_alive", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_npcs_name"),
    )
    op.create_table(
        "quests",
        *_audit_columns(),
        sa.Column("title", sa.String(140), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location_id", sa.Uuid(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("giver_npc_id", sa.Uuid(), sa.ForeignKey("npcs.id"), nullable=True),
        sa.Column("faction_id", sa.Uuid(), sa.ForeignKey("factions.id"), nullable=True),
        sa.Column("minimum_level", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("prerequisites", _json(), nullable=False),
        sa.Column("rewards", _json(), nullable=False),
        sa.Column("repeatable", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint("minimum_level >= 1", name="ck_quests_level"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title", name="uq_quests_title"),
    )
    op.create_index("ix_quests_location_id", "quests", ["location_id"])
    op.create_table(
        "quest_steps",
        *_audit_columns(),
        sa.Column(
            "quest_id",
            sa.Uuid(),
            sa.ForeignKey("quests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.SmallInteger(), nullable=False),
        sa.Column("objective_type", sa.String(40), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_count", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint("sequence >= 0", name="ck_quest_steps_sequence"),
        sa.CheckConstraint("required_count > 0", name="ck_quest_steps_required"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quest_id", "sequence", name="uq_quest_steps_sequence"),
    )
    op.create_index("ix_quest_steps_quest_id", "quest_steps", ["quest_id"])


def _create_player_state_tables() -> None:
    op.create_table(
        "character_factions",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("faction_id", sa.Uuid(), sa.ForeignKey("factions.id"), nullable=False),
        sa.Column("reputation", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rank", sa.String(40), server_default="OUTSIDER", nullable=False),
        sa.Column("joined", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint(
            "reputation BETWEEN -1000 AND 1000",
            name="ck_character_factions_reputation",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", "faction_id", name="uq_character_factions"),
    )
    op.create_table(
        "character_dungeon_states",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dungeon_id", sa.Uuid(), sa.ForeignKey("dungeons.id"), nullable=False),
        sa.Column("entered", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("cleared", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("boss_alive", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", "dungeon_id", name="uq_character_dungeons"),
    )
    op.create_table(
        "relationships",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("npc_id", sa.Uuid(), sa.ForeignKey("npcs.id"), nullable=False),
        sa.Column("trust", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("friendship", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("respect", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("fear", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("hatred", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("loyalty", sa.SmallInteger(), server_default="0", nullable=False),
        sa.CheckConstraint(
            "trust BETWEEN -100 AND 100 AND friendship BETWEEN -100 AND 100 "
            "AND respect BETWEEN -100 AND 100 AND fear BETWEEN -100 AND 100 "
            "AND hatred BETWEEN -100 AND 100 AND loyalty BETWEEN -100 AND 100",
            name="ck_relationship_values",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", "npc_id", name="uq_relationships"),
    )
    op.create_table(
        "character_quests",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quest_id", sa.Uuid(), sa.ForeignKey("quests.id"), nullable=False),
        sa.Column("status", sa.String(20), server_default="NOT_STARTED", nullable=False),
        sa.Column("current_step", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("step_progress", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "objectives_complete", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column(
            "rewards_claimed", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('NOT_STARTED', 'ACTIVE', 'COMPLETED', 'FAILED', 'ARCHIVED')",
            name="ck_character_quests_status",
        ),
        sa.CheckConstraint(
            "current_step >= 0 AND step_progress >= 0", name="ck_quest_progress"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", "quest_id", name="uq_character_quests"),
    )
    op.create_table(
        "journal_entries",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quest_id", sa.Uuid(), sa.ForeignKey("quests.id"), nullable=True),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "world_events",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("location_id", sa.Uuid(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("faction_id", sa.Uuid(), sa.ForeignKey("factions.id"), nullable=True),
        sa.Column("quest_id", sa.Uuid(), sa.ForeignKey("quests.id"), nullable=True),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("deduplication_key", sa.String(180), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deduplication_key", name="uq_world_events_deduplication"),
    )
    for table, columns in {
        "character_factions": ("player_id", "character_id", "faction_id"),
        "character_dungeon_states": ("player_id", "character_id", "dungeon_id"),
        "relationships": ("player_id", "character_id", "npc_id"),
        "character_quests": ("player_id", "character_id", "quest_id"),
        "journal_entries": ("player_id", "character_id"),
        "world_events": ("player_id", "character_id", "event_type"),
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column])


def _seed_content() -> None:
    factions = sa.table(
        "factions",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
    )
    op.bulk_insert(
        factions,
        [
            {
                "id": FACTION_ID,
                "name": "Frontier Wardens",
                "description": "Scouts and protectors who keep the frontier roads open.",
            }
        ],
    )
    dungeons = sa.table(
        "dungeons",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("location_id", sa.Uuid()),
        sa.column("recommended_level", sa.SmallInteger()),
    )
    op.bulk_insert(
        dungeons,
        [
            {
                "id": DUNGEON_ID,
                "name": "Rootbound Hollow",
                "description": "A sealed hollow beneath the old crossroads.",
                "location_id": CROSSROADS_ID,
                "recommended_level": 1,
            }
        ],
    )
    npcs = sa.table(
        "npcs",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("race_id", sa.Uuid()),
        sa.column("faction_id", sa.Uuid()),
        sa.column("home_location_id", sa.Uuid()),
        sa.column("occupation", sa.String()),
        sa.column("role", sa.String()),
        sa.column("personality_profile", _json()),
        sa.column("schedule", _json()),
        sa.column("knowledge", _json()),
        sa.column("is_alive", sa.Boolean()),
    )
    op.bulk_insert(
        npcs,
        [
            {
                "id": NPC_ID,
                "name": "Warden Elian",
                "race_id": HUMAN_ID,
                "faction_id": FACTION_ID,
                "home_location_id": GREENWOOD_ID,
                "occupation": "Frontier Warden",
                "role": "QUEST_GIVER",
                "personality_profile": {
                    "archetype": "watchful_scout",
                    "traits": ["practical", "protective"],
                    "speech_style": "direct",
                    "values": ["duty", "safety"],
                },
                "schedule": [
                    {"start_hour": 0, "end_hour": 24, "location_id": GREENWOOD_ID}
                ],
                "knowledge": {
                    "locations": [GREENWOOD_ID, CROSSROADS_ID],
                    "factions": [FACTION_ID],
                    "topics": ["rootbound_hollow", "frontier_patrol"],
                },
                "is_alive": True,
            }
        ],
    )
    quests = sa.table(
        "quests",
        sa.column("id", sa.Uuid()),
        sa.column("title", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("location_id", sa.Uuid()),
        sa.column("giver_npc_id", sa.Uuid()),
        sa.column("faction_id", sa.Uuid()),
        sa.column("minimum_level", sa.SmallInteger()),
        sa.column("prerequisites", _json()),
        sa.column("rewards", _json()),
        sa.column("repeatable", sa.Boolean()),
    )
    op.bulk_insert(
        quests,
        [
            {
                "id": QUEST_ID,
                "title": "The Rootbound Watch",
                "description": "Aid Warden Elian, then secure the Rootbound Hollow.",
                "location_id": GREENWOOD_ID,
                "giver_npc_id": NPC_ID,
                "faction_id": FACTION_ID,
                "minimum_level": 1,
                "prerequisites": [],
                "rewards": {"experience": 120, "gold": 45, "reputation": 20},
                "repeatable": False,
            }
        ],
    )
    steps = sa.table(
        "quest_steps",
        sa.column("quest_id", sa.Uuid()),
        sa.column("sequence", sa.SmallInteger()),
        sa.column("objective_type", sa.String()),
        sa.column("target_id", sa.Uuid()),
        sa.column("description", sa.Text()),
        sa.column("required_count", sa.Integer()),
    )
    op.bulk_insert(
        steps,
        [
            {
                "quest_id": QUEST_ID,
                "sequence": 0,
                "objective_type": "NPC_HELP",
                "target_id": NPC_ID,
                "description": "Offer practical aid to Warden Elian.",
                "required_count": 1,
            },
            {
                "quest_id": QUEST_ID,
                "sequence": 1,
                "objective_type": "DUNGEON_CLEAR",
                "target_id": DUNGEON_ID,
                "description": "Clear the Rootbound Hollow.",
                "required_count": 1,
            },
        ],
    )


def upgrade() -> None:
    """Create and seed the bounded v0.7 world foundation."""
    _create_world_tables()
    _create_player_state_tables()
    _seed_content()
    for table in (
        "factions",
        "dungeons",
        "npcs",
        "quests",
        "quest_steps",
        "character_factions",
        "character_dungeon_states",
        "relationships",
        "character_quests",
        "journal_entries",
        "world_events",
    ):
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """)


def downgrade() -> None:
    """Remove v0.7 state without altering earlier release data."""
    for table in (
        "world_events",
        "journal_entries",
        "character_quests",
        "relationships",
        "character_dungeon_states",
        "character_factions",
        "quest_steps",
        "quests",
        "npcs",
        "dungeons",
        "factions",
    ):
        op.drop_table(table)
