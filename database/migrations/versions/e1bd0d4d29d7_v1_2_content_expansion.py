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

# Existing IDs
HUMAN_ID = "51000000-0000-0000-0000-000000000001"
GREENWOOD_ID = "56000000-0000-0000-0000-000000000002"
VALERIS_ID = "56000000-0000-0000-0000-000000000005"
SILAS_ID = "74000000-0000-0000-0000-000000000002"
HAGAR_ID = "74000000-0000-0000-0000-000000000006"
KAEL_ID = "74000000-0000-0000-0000-000000000007"

# New IDs for v1.2
ELENA_ID = "74000000-0000-0000-0000-000000000008"
SHOP_SILAS_ID = "80000000-0000-0000-0000-000000000001"
ITEM_GREATER_POTION_ID = "54000000-0000-0000-0000-000000000010"
ITEM_STEEL_SWORD_ID = "54000000-0000-0000-0000-000000000011"
ITEM_IRON_SHIELD_ID = "54000000-0000-0000-0000-000000000012"
QUEST_BLACKSMITH_ID = "75000000-0000-0000-0000-000000000008"
QUEST_SCOUT_ID = "75000000-0000-0000-0000-000000000009"


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
    op.execute(
        sa.text(
            "INSERT INTO shops (id, owner_npc_id, name, description) "
            "VALUES (:id, :owner, :name, :desc)"
        ).bindparams(
            id=SHOP_SILAS_ID,
            owner=SILAS_ID,
            name="Silas's Sundries",
            desc="Silas offers various wares for the traveling adventurer.",
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO shop_items (shop_id, item_id, price) "
            "VALUES (:shop, :item, :price)"
        ).bindparams(
            shop=SHOP_SILAS_ID,
            item=ITEM_GREATER_POTION_ID,
            price=100,
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO shop_items (shop_id, item_id, price) "
            "VALUES (:shop, :item, :price)"
        ).bindparams(
            shop=SHOP_SILAS_ID,
            item=ITEM_STEEL_SWORD_ID,
            price=450,
        )
    )

    # 4. Add Innkeeper Elena
    op.execute(
        sa.text(
            "INSERT INTO npcs (id, name, race_id, home_location_id, occupation, role, personality_profile, schedule, knowledge, is_alive) "
            "VALUES (:id, :name, :race, :loc, :occ, :role, :pers, :sched, :know, :alive)"
        ).bindparams(
            id=ELENA_ID,
            name="Innkeeper Elena",
            race=HUMAN_ID,
            loc=GREENWOOD_ID,
            occ="Innkeeper",
            role="INNKEEPER",
            pers=_json().result_processor(None, None)({"archetype": "hospitable_host"}),
            sched=_json().result_processor(None, None)(
                [{"start_hour": 0, "end_hour": 24, "location_id": GREENWOOD_ID}]
            ),
            know=_json().result_processor(None, None)(
                {"topics": ["resting", "local_rumors"]}
            ),
            alive=True,
        )
    )

    # 5. Add v1.2 Quests
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
                "faction_id": "72000000-0000-0000-0000-000000000001",
                "minimum_level": 3,
                "prerequisites": ["75000000-0000-0000-0000-000000000006"],
                "rewards": {"experience": 300, "gold": 150, "reputation": 60},
                "repeatable": False,
            },
        ],
    )

    # Quest Steps
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
                "quest_id": QUEST_BLACKSMITH_ID,
                "sequence": 0,
                "objective_type": "NPC_HELP",
                "target_id": HAGAR_ID,
                "description": "Discuss the alloy with Hagar.",
                "required_count": 1,
            },
            {
                "quest_id": QUEST_SCOUT_ID,
                "sequence": 0,
                "objective_type": "NPC_HELP",
                "target_id": KAEL_ID,
                "description": "Receive the scouting orders from Kael.",
                "required_count": 1,
            },
        ],
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
        sa.text("DELETE FROM quest_steps WHERE quest_id IN (:q1, :q2)").bindparams(
            q1=QUEST_BLACKSMITH_ID, q2=QUEST_SCOUT_ID
        )
    )
    op.execute(
        sa.text("DELETE FROM quests WHERE id IN (:q1, :q2)").bindparams(
            q1=QUEST_BLACKSMITH_ID, q2=QUEST_SCOUT_ID
        )
    )
    op.execute(sa.text("DELETE FROM npcs WHERE id = :id").bindparams(id=ELENA_ID))
    op.drop_table("shop_items")
    op.drop_table("shops")
    op.execute(
        sa.text("DELETE FROM items WHERE id IN (:i1, :i2, :i3)").bindparams(
            i1=ITEM_GREATER_POTION_ID, i2=ITEM_STEEL_SWORD_ID, i3=ITEM_IRON_SHIELD_ID
        )
    )
