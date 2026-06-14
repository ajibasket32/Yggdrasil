"""Create deterministic character, progression, inventory, and navigation state.

Revision ID: 0003_character_system
Revises: 0002_rag_memory
Create Date: 2026-06-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_character_system"
down_revision: str | None = "0002_rag_memory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


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


def _create_definition_tables() -> None:
    op.create_table(
        "races",
        *_audit_columns(),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("lore", sa.Text(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("selectable", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("base_stats", _json(), nullable=False),
        sa.Column("racial_bonuses", _json(), nullable=False),
        sa.Column("racial_penalties", _json(), nullable=False),
        sa.Column("racial_passives", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_races_name"),
    )
    op.create_table(
        "jobs",
        *_audit_columns(),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("lore", sa.Text(), nullable=False),
        sa.Column("tier", sa.String(20), nullable=False),
        sa.Column("max_level", sa.SmallInteger(), nullable=False),
        sa.Column(
            "selectable_at_creation",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("prerequisites", _json(), nullable=False),
        sa.Column("skill_unlocks", _json(), nullable=False),
        sa.Column("passive_unlocks", _json(), nullable=False),
        sa.Column("stat_modifiers", _json(), nullable=False),
        sa.CheckConstraint(
            "tier IN ('BASIC', 'HIGH', 'RARE', 'WORLD')",
            name="ck_jobs_tier",
        ),
        sa.CheckConstraint("max_level BETWEEN 1 AND 15", name="ck_jobs_max_level"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_jobs_name"),
    )
    op.create_table(
        "skills",
        *_audit_columns(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("skill_type", sa.String(30), nullable=False),
        sa.Column("mana_cost", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cooldown", sa.Integer(), server_default="0", nullable=False),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("effect_definitions", _json(), nullable=False),
        sa.CheckConstraint("mana_cost >= 0", name="ck_skills_mana_cost"),
        sa.CheckConstraint("cooldown >= 0", name="ck_skills_cooldown"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_skills_name"),
    )
    op.create_table(
        "job_skills",
        *_audit_columns(),
        sa.Column(
            "job_id",
            sa.Uuid(),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("required_level", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("required_level >= 1", name="ck_job_skills_required_level"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),
    )
    op.create_index("ix_job_skills_job_id", "job_skills", ["job_id"])
    op.create_index("ix_job_skills_skill_id", "job_skills", ["skill_id"])

    op.create_table(
        "locations",
        *_audit_columns(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("location_type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("danger_level", sa.SmallInteger(), nullable=False),
        sa.Column(
            "is_starting_location",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_locations_name"),
    )
    op.create_table(
        "location_routes",
        *_audit_columns(),
        sa.Column(
            "origin_location_id",
            sa.Uuid(),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "destination_location_id",
            sa.Uuid(),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("travel_cost", sa.Integer(), server_default="1", nullable=False),
        sa.Column("requirements", _json(), nullable=False),
        sa.CheckConstraint("travel_cost >= 0", name="ck_location_routes_cost"),
        sa.CheckConstraint(
            "origin_location_id <> destination_location_id",
            name="ck_location_routes_distinct",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "origin_location_id",
            "destination_location_id",
            name="uq_location_routes_edge",
        ),
    )
    op.create_index(
        "ix_location_routes_origin_location_id",
        "location_routes",
        ["origin_location_id"],
    )
    op.create_index(
        "ix_location_routes_destination_location_id",
        "location_routes",
        ["destination_location_id"],
    )

    op.create_table(
        "items",
        *_audit_columns(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("lore", sa.Text(), nullable=False),
        sa.Column("item_type", sa.String(30), nullable=False),
        sa.Column("rarity", sa.String(20), nullable=False),
        sa.Column("weight", sa.Numeric(10, 2), nullable=False),
        sa.Column("base_value", sa.Integer(), nullable=False),
        sa.Column("base_stats", _json(), nullable=False),
        sa.Column("compatible_slots", _json(), nullable=False),
        sa.Column("is_stackable", sa.Boolean(), nullable=False),
        sa.Column("max_stack", sa.Integer(), nullable=False),
        sa.Column("is_quest_item", sa.Boolean(), nullable=False),
        sa.Column("is_droppable", sa.Boolean(), nullable=False),
        sa.Column("required_level", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint("weight >= 0", name="ck_items_weight"),
        sa.CheckConstraint("base_value >= 0", name="ck_items_value"),
        sa.CheckConstraint("max_stack >= 1", name="ck_items_max_stack"),
        sa.CheckConstraint("required_level >= 1", name="ck_items_required_level"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_items_name"),
    )
    op.create_table(
        "equipment_slots",
        *_audit_columns(),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_equipment_slots_code"),
        sa.UniqueConstraint("name", name="uq_equipment_slots_name"),
    )


def _create_character_tables() -> None:
    op.create_table(
        "characters",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(32), nullable=False),
        sa.Column("race_id", sa.Uuid(), sa.ForeignKey("races.id"), nullable=False),
        sa.Column("active_job_id", sa.Uuid(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column(
            "current_location_id",
            sa.Uuid(),
            sa.ForeignKey("locations.id"),
            nullable=False,
        ),
        sa.Column("gender", sa.String(30), nullable=False),
        sa.Column("alignment", sa.String(30), nullable=False),
        sa.Column("level", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("experience", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skill_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("strength", sa.Integer(), nullable=False),
        sa.Column("dexterity", sa.Integer(), nullable=False),
        sa.Column("agility", sa.Integer(), nullable=False),
        sa.Column("vitality", sa.Integer(), nullable=False),
        sa.Column("intelligence", sa.Integer(), nullable=False),
        sa.Column("wisdom", sa.Integer(), nullable=False),
        sa.Column("charisma", sa.Integer(), nullable=False),
        sa.Column("current_hp", sa.Integer(), nullable=False),
        sa.Column("current_mp", sa.Integer(), nullable=False),
        sa.Column("current_stamina", sa.Integer(), nullable=False),
        sa.Column("gold", sa.Integer(), server_default="0", nullable=False),
        sa.Column("fame", sa.Integer(), server_default="0", nullable=False),
        sa.Column("karma", sa.Integer(), server_default="0", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("level BETWEEN 1 AND 100", name="ck_characters_level"),
        sa.CheckConstraint("experience >= 0", name="ck_characters_experience"),
        sa.CheckConstraint("karma BETWEEN -500 AND 500", name="ck_characters_karma"),
        sa.CheckConstraint(
            "current_hp >= 0 AND current_mp >= 0 AND current_stamina >= 0",
            name="ck_characters_resources",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_id", "name", name="uq_characters_player_name"),
    )
    for column in (
        "player_id",
        "race_id",
        "active_job_id",
        "current_location_id",
    ):
        op.create_index(f"ix_characters_{column}", "characters", [column])

    op.create_table(
        "character_jobs",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("job_level", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("experience", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint("job_level >= 1", name="ck_character_jobs_level"),
        sa.CheckConstraint("experience >= 0", name="ck_character_jobs_experience"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", "job_id", name="uq_character_jobs"),
    )
    op.create_index("ix_character_jobs_player_id", "character_jobs", ["player_id"])
    op.create_index(
        "ix_character_jobs_character_id", "character_jobs", ["character_id"]
    )
    op.create_index("ix_character_jobs_job_id", "character_jobs", ["job_id"])

    op.create_table(
        "character_skills",
        *_audit_columns(),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_id", sa.Uuid(), sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("skill_level", sa.SmallInteger(), server_default="1", nullable=False),
        sa.CheckConstraint("skill_level >= 1", name="ck_character_skills_level"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "character_id",
            "skill_id",
            name="uq_character_skills_character_skill",
        ),
    )
    op.create_index(
        "ix_character_skills_character_id", "character_skills", ["character_id"]
    )
    op.create_index("ix_character_skills_skill_id", "character_skills", ["skill_id"])

    op.create_table(
        "inventories",
        *_audit_columns(),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("slot_count", sa.Integer(), server_default="40", nullable=False),
        sa.Column("max_weight", sa.Numeric(10, 2), nullable=False),
        sa.CheckConstraint("slot_count > 0", name="ck_inventories_slots"),
        sa.CheckConstraint("max_weight > 0", name="ck_inventories_weight"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", name="uq_inventories_character"),
    )
    op.create_index("ix_inventories_character_id", "inventories", ["character_id"])
    op.create_table(
        "inventory_items",
        *_audit_columns(),
        sa.Column(
            "inventory_id",
            sa.Uuid(),
            sa.ForeignKey("inventories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_id", sa.Uuid(), sa.ForeignKey("items.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("slot_index", sa.Integer(), nullable=False),
        sa.Column("unique_instance_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_items_quantity"),
        sa.CheckConstraint("slot_index >= 0", name="ck_inventory_items_slot"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "inventory_id", "slot_index", name="uq_inventory_items_slot"
        ),
    )
    op.create_index(
        "ix_inventory_items_inventory_id", "inventory_items", ["inventory_id"]
    )
    op.create_index("ix_inventory_items_item_id", "inventory_items", ["item_id"])
    op.create_index(
        "uq_inventory_items_unique_instance",
        "inventory_items",
        ["unique_instance_id"],
        unique=True,
        postgresql_where=sa.text("unique_instance_id IS NOT NULL"),
    )
    op.create_table(
        "equipped_items",
        *_audit_columns(),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "slot_id",
            sa.Uuid(),
            sa.ForeignKey("equipment_slots.id"),
            nullable=False,
        ),
        sa.Column(
            "inventory_item_id",
            sa.Uuid(),
            sa.ForeignKey("inventory_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", "slot_id", name="uq_equipped_items_slot"),
        sa.UniqueConstraint(
            "inventory_item_id", name="uq_equipped_items_inventory_item"
        ),
    )
    op.create_index(
        "ix_equipped_items_character_id", "equipped_items", ["character_id"]
    )
    op.create_index("ix_equipped_items_slot_id", "equipped_items", ["slot_id"])

    op.create_table(
        "character_location_discoveries",
        *_audit_columns(),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.Uuid(),
            sa.ForeignKey("locations.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "character_id",
            "location_id",
            name="uq_character_location_discoveries",
        ),
    )
    op.create_index(
        "ix_character_location_discoveries_character_id",
        "character_location_discoveries",
        ["character_id"],
    )
    op.create_index(
        "ix_character_location_discoveries_location_id",
        "character_location_discoveries",
        ["location_id"],
    )


RACE_IDS = {
    "human": "51000000-0000-0000-0000-000000000001",
    "elf": "51000000-0000-0000-0000-000000000002",
    "dwarf": "51000000-0000-0000-0000-000000000003",
    "skeleton": "51000000-0000-0000-0000-000000000004",
}
JOB_IDS = {
    "warrior": "52000000-0000-0000-0000-000000000001",
    "mage": "52000000-0000-0000-0000-000000000002",
    "cleric": "52000000-0000-0000-0000-000000000003",
    "rogue": "52000000-0000-0000-0000-000000000004",
    "archer": "52000000-0000-0000-0000-000000000005",
    "monk": "52000000-0000-0000-0000-000000000006",
    "druid": "52000000-0000-0000-0000-000000000007",
    "alchemist": "52000000-0000-0000-0000-000000000008",
    "paladin": "52000000-0000-0000-0000-000000000009",
}
SKILL_IDS = {
    "power_strike": "53000000-0000-0000-0000-000000000001",
    "ember": "53000000-0000-0000-0000-000000000002",
    "mend": "53000000-0000-0000-0000-000000000003",
    "quick_step": "53000000-0000-0000-0000-000000000004",
    "steady_aim": "53000000-0000-0000-0000-000000000005",
    "iron_body": "53000000-0000-0000-0000-000000000006",
    "vine_guard": "53000000-0000-0000-0000-000000000007",
    "field_mixture": "53000000-0000-0000-0000-000000000008",
    "radiant_guard": "53000000-0000-0000-0000-000000000009",
}
ITEM_IDS = {
    "potion": "54000000-0000-0000-0000-000000000001",
    "iron_sword": "54000000-0000-0000-0000-000000000002",
    "traveler_seal": "54000000-0000-0000-0000-000000000003",
    "world_stone": "54000000-0000-0000-0000-000000000004",
    "eternity_bloom": "54000000-0000-0000-0000-000000000005",
    "dragon_scale": "54000000-0000-0000-0000-000000000006",
}
SLOT_IDS = {
    "main_hand": "55000000-0000-0000-0000-000000000001",
    "off_hand": "55000000-0000-0000-0000-000000000002",
    "helmet": "55000000-0000-0000-0000-000000000003",
    "chest": "55000000-0000-0000-0000-000000000004",
    "boots": "55000000-0000-0000-0000-000000000005",
    "ring_1": "55000000-0000-0000-0000-000000000006",
    "ring_2": "55000000-0000-0000-0000-000000000007",
    "artifact": "55000000-0000-0000-0000-000000000008",
}
LOCATION_IDS = {
    "frontier_gate": "56000000-0000-0000-0000-000000000001",
    "greenwood": "56000000-0000-0000-0000-000000000002",
    "stonewatch": "56000000-0000-0000-0000-000000000003",
    "ancient_crossroads": "56000000-0000-0000-0000-000000000004",
    "valeris": "56000000-0000-0000-0000-000000000005",
}


def _seed_definitions() -> None:
    races = sa.table(
        "races",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("lore", sa.Text()),
        sa.column("category", sa.String()),
        sa.column("selectable", sa.Boolean()),
        sa.column("base_stats", _json()),
        sa.column("racial_bonuses", _json()),
        sa.column("racial_penalties", _json()),
        sa.column("racial_passives", _json()),
    )
    base = {
        "strength": 10,
        "dexterity": 10,
        "agility": 10,
        "vitality": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10,
    }
    op.bulk_insert(
        races,
        [
            {
                "id": RACE_IDS["human"],
                "name": "Human",
                "description": "Adaptable humanoids with broad job access.",
                "lore": "Human communities thrive through flexibility and resolve.",
                "category": "HUMANOID",
                "selectable": True,
                "base_stats": base,
                "racial_bonuses": {"charisma": 1},
                "racial_penalties": {},
                "racial_passives": ["adaptable"],
            },
            {
                "id": RACE_IDS["elf"],
                "name": "Elf",
                "description": "Agile humanoids attuned to magic and wilderness.",
                "lore": "Elven paths value patience, precision, and old knowledge.",
                "category": "HUMANOID",
                "selectable": True,
                "base_stats": base,
                "racial_bonuses": {"agility": 2, "intelligence": 1},
                "racial_penalties": {"vitality": 1},
                "racial_passives": ["keen_senses"],
            },
            {
                "id": RACE_IDS["dwarf"],
                "name": "Dwarf",
                "description": "Sturdy humanoids shaped by stone and craft.",
                "lore": "Dwarven holds preserve craft traditions across generations.",
                "category": "HUMANOID",
                "selectable": True,
                "base_stats": base,
                "racial_bonuses": {"strength": 1, "vitality": 2},
                "racial_penalties": {"agility": 1},
                "racial_passives": ["stone_resolve"],
            },
            {
                "id": RACE_IDS["skeleton"],
                "name": "Skeleton",
                "description": "An undead heteromorph sustained by negative energy.",
                "lore": "Some awakened bones retain will beyond the grave.",
                "category": "HETEROMORPHIC",
                "selectable": True,
                "base_stats": base,
                "racial_bonuses": {"vitality": 2, "wisdom": 1},
                "racial_penalties": {"charisma": 2},
                "racial_passives": ["undead_body", "poison_immunity"],
            },
        ],
    )

    jobs = sa.table(
        "jobs",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("lore", sa.Text()),
        sa.column("tier", sa.String()),
        sa.column("max_level", sa.SmallInteger()),
        sa.column("selectable_at_creation", sa.Boolean()),
        sa.column("prerequisites", _json()),
        sa.column("skill_unlocks", _json()),
        sa.column("passive_unlocks", _json()),
        sa.column("stat_modifiers", _json()),
    )
    job_rows = [
        ("warrior", "Warrior", {"strength": 3, "vitality": 2, "agility": 1}),
        ("mage", "Mage", {"intelligence": 4, "wisdom": 2}),
        ("cleric", "Cleric", {"wisdom": 3, "vitality": 2, "charisma": 1}),
        ("rogue", "Rogue", {"dexterity": 3, "agility": 3}),
        ("archer", "Archer", {"dexterity": 3, "agility": 2, "wisdom": 1}),
        ("monk", "Monk", {"strength": 2, "agility": 2, "vitality": 2}),
        ("druid", "Druid", {"wisdom": 3, "intelligence": 2, "vitality": 1}),
        ("alchemist", "Alchemist", {"intelligence": 3, "dexterity": 2, "wisdom": 1}),
    ]
    op.bulk_insert(
        jobs,
        [
            {
                "id": JOB_IDS[key],
                "name": name,
                "description": f"Basic {name.lower()} training.",
                "lore": f"The {name} path is taught throughout the frontier.",
                "tier": "BASIC",
                "max_level": 15,
                "selectable_at_creation": True,
                "prerequisites": {},
                "skill_unlocks": [
                    {"skill_id": SKILL_IDS[list(SKILL_IDS)[index]], "level": 1}
                ],
                "passive_unlocks": [],
                "stat_modifiers": modifiers,
            }
            for index, (key, name, modifiers) in enumerate(job_rows)
        ]
        + [
            {
                "id": JOB_IDS["paladin"],
                "name": "Paladin",
                "description": "A high job combining martial and sacred discipline.",
                "lore": "Paladins bind strength to duty rather than conquest.",
                "tier": "HIGH",
                "max_level": 10,
                "selectable_at_creation": False,
                "prerequisites": {
                    "all": [
                        {
                            "job_level": {
                                "job_id": JOB_IDS["warrior"],
                                "minimum": 10,
                            }
                        },
                        {
                            "any": [
                                {
                                    "job_level": {
                                        "job_id": JOB_IDS["cleric"],
                                        "minimum": 5,
                                    }
                                },
                                {"karma_at_least": 100},
                            ]
                        },
                    ]
                },
                "skill_unlocks": [{"skill_id": SKILL_IDS["radiant_guard"], "level": 1}],
                "passive_unlocks": [{"code": "sacred_discipline", "level": 3}],
                "stat_modifiers": {"strength": 2, "vitality": 3, "wisdom": 2},
            }
        ],
    )

    skills = sa.table(
        "skills",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("skill_type", sa.String()),
        sa.column("mana_cost", sa.Integer()),
        sa.column("cooldown", sa.Integer()),
        sa.column("target_type", sa.String()),
        sa.column("effect_definitions", _json()),
    )
    skill_rows = [
        ("power_strike", "Power Strike", "ACTIVE", 0, "ENEMY", "physical"),
        ("ember", "Ember", "ACTIVE", 5, "ENEMY", "fire"),
        ("mend", "Mend", "ACTIVE", 6, "ALLY", "healing"),
        ("quick_step", "Quick Step", "PASSIVE", 0, "SELF", "agility"),
        ("steady_aim", "Steady Aim", "PASSIVE", 0, "SELF", "accuracy"),
        ("iron_body", "Iron Body", "PASSIVE", 0, "SELF", "defense"),
        ("vine_guard", "Vine Guard", "ACTIVE", 4, "ALLY", "barrier"),
        ("field_mixture", "Field Mixture", "ACTIVE", 3, "ALLY", "healing"),
        ("radiant_guard", "Radiant Guard", "ACTIVE", 8, "ALLY", "barrier"),
    ]
    op.bulk_insert(
        skills,
        [
            {
                "id": SKILL_IDS[key],
                "name": name,
                "description": f"Deterministic {name.lower()} skill.",
                "skill_type": skill_type,
                "mana_cost": mana,
                "cooldown": 0,
                "target_type": target,
                "effect_definitions": [{"effect": effect, "magnitude": 1}],
            }
            for key, name, skill_type, mana, target, effect in skill_rows
        ],
    )

    job_skills = sa.table(
        "job_skills",
        sa.column("job_id", sa.Uuid()),
        sa.column("skill_id", sa.Uuid()),
        sa.column("required_level", sa.SmallInteger()),
    )
    op.bulk_insert(
        job_skills,
        [
            {
                "job_id": JOB_IDS[job_key],
                "skill_id": SKILL_IDS[skill_key],
                "required_level": 1,
            }
            for job_key, skill_key in zip(
                JOB_IDS,
                SKILL_IDS,
                strict=True,
            )
        ],
    )

    items = sa.table(
        "items",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("lore", sa.Text()),
        sa.column("item_type", sa.String()),
        sa.column("rarity", sa.String()),
        sa.column("weight", sa.Numeric()),
        sa.column("base_value", sa.Integer()),
        sa.column("base_stats", _json()),
        sa.column("compatible_slots", _json()),
        sa.column("is_stackable", sa.Boolean()),
        sa.column("max_stack", sa.Integer()),
        sa.column("is_quest_item", sa.Boolean()),
        sa.column("is_droppable", sa.Boolean()),
        sa.column("required_level", sa.Integer()),
    )
    op.bulk_insert(
        items,
        [
            {
                "id": ITEM_IDS["potion"],
                "name": "Field Potion",
                "description": "A basic restorative carried by new adventurers.",
                "lore": "Frontier apothecaries seal these bottles with green wax.",
                "item_type": "CONSUMABLE",
                "rarity": "COMMON",
                "weight": 0.5,
                "base_value": 25,
                "base_stats": {"restore_hp": 25},
                "compatible_slots": [],
                "is_stackable": True,
                "max_stack": 20,
                "is_quest_item": False,
                "is_droppable": True,
                "required_level": 1,
            },
            {
                "id": ITEM_IDS["iron_sword"],
                "name": "Frontier Iron Sword",
                "description": "A dependable one-handed training sword.",
                "lore": "Its maker's mark belongs to Stonewatch.",
                "item_type": "WEAPON",
                "rarity": "COMMON",
                "weight": 3.5,
                "base_value": 120,
                "base_stats": {"strength": 2, "physical_attack": 5},
                "compatible_slots": ["main_hand"],
                "is_stackable": False,
                "max_stack": 1,
                "is_quest_item": False,
                "is_droppable": True,
                "required_level": 1,
            },
            {
                "id": ITEM_IDS["traveler_seal"],
                "name": "Traveler Seal",
                "description": "Proof that its bearer entered through the frontier gate.",
                "lore": "The seal records passage without granting rank or reward.",
                "item_type": "QUEST",
                "rarity": "KEY",
                "weight": 0.1,
                "base_value": 0,
                "base_stats": {},
                "compatible_slots": [],
                "is_stackable": False,
                "max_stack": 1,
                "is_quest_item": True,
                "is_droppable": False,
                "required_level": 1,
            },
            {
                "id": ITEM_IDS["world_stone"],
                "name": "World Stone Fragment",
                "description": "A pulsating shard of ancient origin.",
                "lore": "It is said these fragments fell during the Age of Falling Stars.",
                "item_type": "ARTIFACT",
                "rarity": "WORLD",
                "weight": 1.0,
                "base_value": 10000,
                "base_stats": {"magic_attack": 50, "max_mp": 100},
                "compatible_slots": ["artifact"],
                "is_stackable": False,
                "max_stack": 1,
                "is_quest_item": True,
                "is_droppable": False,
                "required_level": 10,
            },
            {
                "id": ITEM_IDS["eternity_bloom"],
                "name": "Eternity Bloom",
                "description": "A flower that never wilts.",
                "lore": "Found only in the deepest parts of the Sylvan Forests.",
                "item_type": "MATERIAL",
                "rarity": "RARE",
                "weight": 0.1,
                "base_value": 500,
                "base_stats": {},
                "compatible_slots": [],
                "is_stackable": True,
                "max_stack": 99,
                "is_quest_item": False,
                "is_droppable": True,
                "required_level": 1,
            },
            {
                "id": ITEM_IDS["dragon_scale"],
                "name": "Dragon Scale",
                "description": "A hard, shimmering scale from a dragon.",
                "lore": "Harvested from the remains of ancient guardians.",
                "item_type": "MATERIAL",
                "rarity": "EPIC",
                "weight": 2.0,
                "base_value": 2500,
                "base_stats": {},
                "compatible_slots": [],
                "is_stackable": True,
                "max_stack": 10,
                "is_quest_item": False,
                "is_droppable": True,
                "required_level": 5,
            },
        ],
    )

    slots = sa.table(
        "equipment_slots",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
    )
    op.bulk_insert(
        slots,
        [
            {"id": slot_id, "code": code, "name": code.replace("_", " ").title()}
            for code, slot_id in SLOT_IDS.items()
        ],
    )

    locations = sa.table(
        "locations",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("location_type", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("danger_level", sa.SmallInteger()),
        sa.column("is_starting_location", sa.Boolean()),
    )
    op.bulk_insert(
        locations,
        [
            {
                "id": LOCATION_IDS["frontier_gate"],
                "name": "Valeris Outskirts",
                "location_type": "SETTLEMENT",
                "description": "The modest beginning of the road to the capital of Valeria.",
                "danger_level": 0,
                "is_starting_location": True,
            },
            {
                "id": LOCATION_IDS["greenwood"],
                "name": "Valerian Forest",
                "location_type": "WILDERNESS",
                "description": "A dense, ancient forest teeming with both life and danger.",
                "danger_level": 1,
                "is_starting_location": False,
            },
            {
                "id": LOCATION_IDS["stonewatch"],
                "name": "Stonewatch Mine",
                "location_type": "SETTLEMENT",
                "description": "A vital source of iron and stone for the kingdom.",
                "danger_level": 0,
                "is_starting_location": False,
            },
            {
                "id": LOCATION_IDS["ancient_crossroads"],
                "name": "Ancient Valerian Crossroads",
                "location_type": "LANDMARK",
                "description": "A historic junction where the three main roads of the region meet.",
                "danger_level": 2,
                "is_starting_location": False,
            },
            {
                "id": LOCATION_IDS["valeris"],
                "name": "Valeris City",
                "location_type": "SETTLEMENT",
                "description": "The magnificent capital of the Kingdom of Valeria.",
                "danger_level": 0,
                "is_starting_location": False,
            },
        ],
    )
    routes = sa.table(
        "location_routes",
        sa.column("origin_location_id", sa.Uuid()),
        sa.column("destination_location_id", sa.Uuid()),
        sa.column("travel_cost", sa.Integer()),
        sa.column("requirements", _json()),
    )
    edges = [
        ("frontier_gate", "greenwood", 1),
        ("greenwood", "frontier_gate", 1),
        ("frontier_gate", "stonewatch", 2),
        ("stonewatch", "frontier_gate", 2),
        ("greenwood", "ancient_crossroads", 2),
        ("ancient_crossroads", "greenwood", 2),
        ("frontier_gate", "valeris", 3),
        ("valeris", "frontier_gate", 3),
    ]
    op.bulk_insert(
        routes,
        [
            {
                "origin_location_id": LOCATION_IDS[origin],
                "destination_location_id": LOCATION_IDS[destination],
                "travel_cost": cost,
                "requirements": {},
            }
            for origin, destination, cost in edges
        ],
    )


def upgrade() -> None:
    """Create and seed the complete v0.5 canonical gameplay foundation."""
    _create_definition_tables()
    _create_character_tables()
    _seed_definitions()

    tables = (
        "races",
        "jobs",
        "skills",
        "job_skills",
        "locations",
        "location_routes",
        "items",
        "equipment_slots",
        "characters",
        "character_jobs",
        "character_skills",
        "inventories",
        "inventory_items",
        "equipped_items",
        "character_location_discoveries",
    )
    for table in tables:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """)


def downgrade() -> None:
    """Remove v0.5 gameplay state without changing prior release tables."""
    for table in (
        "character_location_discoveries",
        "equipped_items",
        "inventory_items",
        "inventories",
        "character_skills",
        "character_jobs",
        "characters",
        "equipment_slots",
        "items",
        "location_routes",
        "locations",
        "job_skills",
        "skills",
        "jobs",
        "races",
    ):
        op.drop_table(table)
