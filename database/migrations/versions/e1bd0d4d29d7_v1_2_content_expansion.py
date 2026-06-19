"""v1.2 content expansion

Revision ID: e1bd0d4d29d7
Revises: 0010_expand_content
Create Date: 2026-06-19 07:36:37.426108
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e1bd0d4d29d7"
down_revision: str | None = "0010_expand_content"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Existing IDs (converted to UUID objects)
HUMAN_ID = UUID("51000000-0000-0000-0000-000000000001")
GREENWOOD_ID = UUID("56000000-0000-0000-0000-000000000002")
VALERIS_ID = UUID("56000000-0000-0000-0000-000000000005")
SILAS_ID = UUID("74000000-0000-0000-0000-000000000002")
HAGAR_ID = UUID("74000000-0000-0000-0000-000000000006")
KAEL_ID = UUID("74000000-0000-0000-0000-000000000007")

# New IDs for v1.2
ELENA_ID = UUID("74000000-0000-0000-0000-000000000008")
SHOP_SILAS_ID = UUID("80000000-0000-0000-0000-000000000001")
ITEM_GREATER_POTION_ID = UUID("54000000-0000-0000-0000-000000000010")
ITEM_STEEL_SWORD_ID = UUID("54000000-0000-0000-0000-000000000011")
ITEM_IRON_SHIELD_ID = UUID("54000000-0000-0000-0000-000000000012")
QUEST_BLACKSMITH_ID = UUID("75000000-0000-0000-0000-000000000008")
QUEST_SCOUT_ID = UUID("75000000-0000-0000-0000-000000000009")


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
    # 1. Create Shop tables
    op.create_table(
        "shops",
        *_audit_columns(),
        sa.Column("owner_npc_id", sa.Uuid(), sa.ForeignKey("npcs.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_npc_id", name="uq_shops_owner"),
    )
    op.create_table(
        "shop_items",
        *_audit_columns(),
        sa.Column("shop_id", sa.Uuid(), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("item_id", sa.Uuid(), sa.ForeignKey("items.id"), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shop_id", "item_id", name="uq_shop_items_shop_item"),
    )

    # 2. Add new items
    items_table = sa.table(
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
        items_table,
        [
            {
                "id": ITEM_GREATER_POTION_ID,
                "name": "Greater Potion",
                "description": "A potent restorative that heals significantly.",
                "lore": "Used by veteran scouts exploring the Sylvan Deep.",
                "item_type": "CONSUMABLE",
                "rarity": "UNCOMMON",
                "weight": 0.5,
                "base_value": 75,
                "base_stats": {"restore_hp": 75},
                "compatible_slots": [],
                "is_stackable": True,
                "max_stack": 20,
                "is_quest_item": False,
                "is_droppable": True,
                "required_level": 1,
            },
            {
                "id": ITEM_STEEL_SWORD_ID,
                "name": "Steel Sword",
                "description": "A sharp, well-balanced steel sword.",
                "lore": "Standard issue for the Valerian Royal Guard.",
                "item_type": "WEAPON",
                "rarity": "UNCOMMON",
                "weight": 4.0,
                "base_value": 350,
                "base_stats": {"strength": 4, "physical_attack": 12},
                "compatible_slots": ["main_hand"],
                "is_stackable": False,
                "max_stack": 1,
                "is_quest_item": False,
                "is_droppable": True,
                "required_level": 3,
            },
            {
                "id": ITEM_IRON_SHIELD_ID,
                "name": "Iron Shield",
                "description": "A heavy iron shield providing solid protection.",
                "lore": "Forged in Stonewatch to withstand heavy blows.",
                "item_type": "ARMOR",
                "rarity": "COMMON",
                "weight": 6.0,
                "base_value": 150,
                "base_stats": {"physical_defense": 8},
                "compatible_slots": ["off_hand"],
                "is_stackable": False,
                "max_stack": 1,
                "is_quest_item": False,
                "is_droppable": True,
                "required_level": 2,
            },
        ],
    )

    # 3. Seed Shop for Silas
    shops_table = sa.table(
        "shops",
        sa.column("id", sa.Uuid()),
        sa.column("owner_npc_id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
    )
    op.bulk_insert(
        shops_table,
        [
            {
                "id": SHOP_SILAS_ID,
                "owner_npc_id": SILAS_ID,
                "name": "Silas's Sundries",
                "description": "Silas offers various wares for the traveling adventurer.",
            }
        ],
    )

    shop_items_table = sa.table(
        "shop_items",
        sa.column("shop_id", sa.Uuid()),
        sa.column("item_id", sa.Uuid()),
        sa.column("price", sa.Integer()),
    )
    op.bulk_insert(
        shop_items_table,
        [
            {
                "shop_id": SHOP_SILAS_ID,
                "item_id": ITEM_GREATER_POTION_ID,
                "price": 100,
            },
            {
                "shop_id": SHOP_SILAS_ID,
                "item_id": ITEM_STEEL_SWORD_ID,
                "price": 450,
            },
        ],
    )

    # 4. Add Innkeeper Elena
    npcs_table = sa.table(
        "npcs",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("race_id", sa.Uuid()),
        sa.column("home_location_id", sa.Uuid()),
        sa.column("occupation", sa.String()),
        sa.column("role", sa.String()),
        sa.column("personality_profile", _json()),
        sa.column("schedule", _json()),
        sa.column("knowledge", _json()),
        sa.column("is_alive", sa.Boolean()),
    )
    op.bulk_insert(
        npcs_table,
        [
            {
                "id": ELENA_ID,
                "name": "Innkeeper Elena",
                "race_id": HUMAN_ID,
                "home_location_id": GREENWOOD_ID,
                "occupation": "Innkeeper",
                "role": "INNKEEPER",
                "personality_profile": {"archetype": "hospitable_host"},
                "schedule": [{"start_hour": 0, "end_hour": 24, "location_id": GREENWOOD_ID}],
                "knowledge": {"topics": ["resting", "local_rumors"]},
                "is_alive": True,
            }
        ],
    )

    # 5. Add v1.2 Quests
    quests_table = sa.table(
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
        quests_table,
        [
            {
                "id": QUEST_BLACKSMITH_ID,
                "title": "The Blacksmith's Request",
                "description": "Hagar needs you to test a new steel alloy.",
                "location_id": VALERIS_ID,
                "giver_npc_id": HAGAR_ID,
                "faction_id": None,
                "minimum_level": 4,
                "prerequisites": ["75000000-0000-0000-0000-000000000005"],
                "rewards": {"experience": 400, "gold": 300, "reputation": 0},
                "repeatable": False,
            },
            {
                "id": QUEST_SCOUT_ID,
                "title": "Scouting the Border",
                "description": "Kael reports strange sightings near the Sylvan Deep.",
                "location_id": GREENWOOD_ID,
                "giver_npc_id": KAEL_ID,
                "faction_id": UUID("72000000-0000-0000-0000-000000000001"),
                "minimum_level": 3,
                "prerequisites": ["75000000-0000-0000-0000-000000000006"],
                "rewards": {"experience": 300, "gold": 150, "reputation": 60},
                "repeatable": False,
            },
        ],
    )

    # Quest Steps (Using a different approach to ensure UUIDs)
    op.execute(
        sa.text(
            "INSERT INTO quest_steps (id, quest_id, sequence, objective_type, target_id, description, required_count) "
            "VALUES (uuid_generate_v4(), :quest_id, 0, 'NPC_HELP', :target_id, 'Discuss the alloy with Hagar.', 1)"
        ).bindparams(quest_id=QUEST_BLACKSMITH_ID, target_id=HAGAR_ID)
    )
    op.execute(
        sa.text(
            "INSERT INTO quest_steps (id, quest_id, sequence, objective_type, target_id, description, required_count) "
            "VALUES (uuid_generate_v4(), :quest_id, 0, 'NPC_HELP', :target_id, 'Receive the scouting orders from Kael.', 1)"
        ).bindparams(quest_id=QUEST_SCOUT_ID, target_id=KAEL_ID)
    )

    # 6. Add Triggers
    for table in ("shops", "shop_items"):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM quest_steps WHERE quest_id IN (CAST(:q1 AS UUID), CAST(:q2 AS UUID))"
        ).bindparams(q1=QUEST_BLACKSMITH_ID, q2=QUEST_SCOUT_ID)
    )
    op.execute(
        sa.text(
            "DELETE FROM quests WHERE id IN (CAST(:q1 AS UUID), CAST(:q2 AS UUID))"
        ).bindparams(q1=QUEST_BLACKSMITH_ID, q2=QUEST_SCOUT_ID)
    )
    op.execute(
        sa.text("DELETE FROM npcs WHERE id = CAST(:id AS UUID)").bindparams(id=ELENA_ID)
    )
    op.drop_table("shop_items")
    op.drop_table("shops")
    op.execute(
        sa.text(
            "DELETE FROM items WHERE id IN (CAST(:i1 AS UUID), CAST(:i2 AS UUID), CAST(:i3 AS UUID))"
        ).bindparams(
            i1=ITEM_GREATER_POTION_ID, i2=ITEM_STEEL_SWORD_ID, i3=ITEM_IRON_SHIELD_ID
        )
    )
