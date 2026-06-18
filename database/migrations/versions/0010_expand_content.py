"""Expand content with new NPCs, quests, monsters, and items for v1.1.

Revision ID: 0010_expand_content
Revises: 0009_crossroads_name
Create Date: 2026-06-18
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "0010_expand_content"
down_revision: str | None = "0009_crossroads_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# IDs from previous migrations
HUMAN_ID = "51000000-0000-0000-0000-000000000001"
DWARF_ID = "51000000-0000-0000-0000-000000000003"
VALERIS_ID = "56000000-0000-0000-0000-000000000005"
GREENWOOD_ID = "56000000-0000-0000-0000-000000000002"
POTION_ID = "54000000-0000-0000-0000-000000000001"

# New IDs for v1.1 content
HAGAR_ID = "74000000-0000-0000-0000-000000000006"
KAEL_ID = "74000000-0000-0000-0000-000000000007"
QUEST_IRON_ID = "75000000-0000-0000-0000-000000000005"
QUEST_RECON_ID = "75000000-0000-0000-0000-000000000006"
QUEST_SIDE_ID = "75000000-0000-0000-0000-000000000007"
WASP_ID = "70000000-0000-0000-0000-000000000003"
SKELETON_MONSTER_ID = "70000000-0000-0000-0000-000000000004"
WASP_ENCOUNTER_ID = "71000000-0000-0000-0000-000000000003"
SKELETON_ENCOUNTER_ID = "71000000-0000-0000-0000-000000000004"
ORE_ID = "54000000-0000-0000-0000-000000000007"
STONE_ID = "54000000-0000-0000-0000-000000000008"
MAP_ID = "54000000-0000-0000-0000-000000000009"
SYLVAN_BRANCH_ID = "56000000-0000-0000-0000-000000000006"


def upgrade() -> None:
    # 1. Add new items
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
        sa.column("base_stats", sa.JSON()),
        sa.column("compatible_slots", sa.JSON()),
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
                "id": ORE_ID,
                "name": "High-Grade Iron Ore",
                "description": "Purified iron ore from the depths of Stonewatch.",
                "lore": "Hagar prefers this ore for royal commissions.",
                "item_type": "MATERIAL",
                "rarity": "UNCOMMON",
                "weight": 5.0,
                "base_value": 50,
                "base_stats": {},
                "compatible_slots": [],
                "is_stackable": True,
                "max_stack": 20,
                "is_quest_item": True,
                "is_droppable": False,
                "required_level": 1,
            },
            {
                "id": STONE_ID,
                "name": "Sharpening Stone",
                "description": "A coarse stone used to maintain blade edges.",
                "lore": "Standard issue for Valerian scouts.",
                "item_type": "CONSUMABLE",
                "rarity": "COMMON",
                "weight": 0.5,
                "base_value": 15,
                "base_stats": {"temporary_atk_bonus": 5},
                "compatible_slots": [],
                "is_stackable": True,
                "max_stack": 10,
                "is_quest_item": False,
                "is_droppable": True,
                "required_level": 1,
            },
            {
                "id": MAP_ID,
                "name": "Scout's Map",
                "description": "A detailed map of the Sylvan Branch.",
                "lore": "Marked with hidden trails known only to the Wardens.",
                "item_type": "QUEST",
                "rarity": "RARE",
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
        ],
    )

    # 2. Add new location and route
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
                "id": SYLVAN_BRANCH_ID,
                "name": "Sylvan Branch",
                "location_type": "WILDERNESS",
                "description": "A winding, sun-dappled path deep within the Valerian Forest.",
                "danger_level": 2,
                "is_starting_location": False,
            }
        ],
    )

    routes = sa.table(
        "location_routes",
        sa.column("origin_location_id", sa.Uuid()),
        sa.column("destination_location_id", sa.Uuid()),
        sa.column("travel_cost", sa.Integer()),
        sa.column("requirements", sa.JSON()),
    )
    op.bulk_insert(
        routes,
        [
            {
                "origin_location_id": GREENWOOD_ID,
                "destination_location_id": SYLVAN_BRANCH_ID,
                "travel_cost": 1,
                "requirements": {},
            },
            {
                "origin_location_id": SYLVAN_BRANCH_ID,
                "destination_location_id": GREENWOOD_ID,
                "travel_cost": 1,
                "requirements": {},
            },
        ],
    )

    # 3. Add new NPCs
    npcs = sa.table(
        "npcs",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("race_id", sa.Uuid()),
        sa.column("faction_id", sa.Uuid()),
        sa.column("home_location_id", sa.Uuid()),
        sa.column("occupation", sa.String()),
        sa.column("role", sa.String()),
        sa.column("personality_profile", sa.JSON()),
        sa.column("schedule", sa.JSON()),
        sa.column("knowledge", sa.JSON()),
        sa.column("is_alive", sa.Boolean()),
    )
    op.bulk_insert(
        npcs,
        [
            {
                "id": HAGAR_ID,
                "name": "Blacksmith Hagar",
                "race_id": DWARF_ID,
                "faction_id": None,
                "home_location_id": VALERIS_ID,
                "occupation": "Royal Blacksmith",
                "role": "QUEST_GIVER",
                "personality_profile": {
                    "archetype": "gruff_artisan",
                    "traits": ["prideful", "honest"],
                    "speech_style": "booming",
                    "values": ["craftsmanship", "loyalty"],
                },
                "schedule": [{"start_hour": 6, "end_hour": 22, "location_id": VALERIS_ID}],
                "knowledge": {
                    "locations": [VALERIS_ID, "56000000-0000-0000-0000-000000000003"],
                    "factions": [],
                    "topics": ["iron_ore", "royal_armory"],
                },
                "is_alive": True,
            },
            {
                "id": KAEL_ID,
                "name": "Scout Kael",
                "race_id": HUMAN_ID,
                "faction_id": "72000000-0000-0000-0000-000000000001",
                "home_location_id": GREENWOOD_ID,
                "occupation": "Forest Scout",
                "role": "QUEST_GIVER",
                "personality_profile": {
                    "archetype": "silent_observer",
                    "traits": ["alert", "cautious"],
                    "speech_style": "whispered",
                    "values": ["nature", "vigilance"],
                },
                "schedule": [{"start_hour": 0, "end_hour": 24, "location_id": GREENWOOD_ID}],
                "knowledge": {
                    "locations": [GREENWOOD_ID, SYLVAN_BRANCH_ID],
                    "factions": ["72000000-0000-0000-0000-000000000001"],
                    "topics": ["sylvan_branch", "wasp_nests"],
                },
                "is_alive": True,
            },
        ],
    )

    # 4. Add new Monsters and Encounters
    monsters = sa.table(
        "monsters",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("level", sa.SmallInteger()),
        sa.column("family", sa.String()),
        sa.column("max_hp", sa.Integer()),
        sa.column("max_mp", sa.Integer()),
        sa.column("max_stamina", sa.Integer()),
        sa.column("combat_stats", sa.JSON()),
        sa.column("resistances", sa.JSON()),
        sa.column("behavior", sa.JSON()),
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
                "id": WASP_ID,
                "name": "Giant Wasp",
                "level": 3,
                "family": "INSECT",
                "max_hp": 70,
                "max_mp": 0,
                "max_stamina": 80,
                "combat_stats": {
                    "physical_attack": 25,
                    "physical_defense": 10,
                    "magic_attack": 5,
                    "magic_defense": 15,
                    "accuracy": 85,
                    "evasion": 20,
                    "critical_chance": 10,
                    "initiative": 25,
                },
                "resistances": {"nature": 50},
                "behavior": {"skill": "STING"},
                "reward_experience": 110,
                "reward_gold": 25,
                "loot_item_id": POTION_ID,
                "loot_chance_percent": 30,
                "escape_blocked": False,
            },
            {
                "id": SKELETON_MONSTER_ID,
                "name": "Ancient Sentry",
                "level": 4,
                "family": "UNDEAD",
                "max_hp": 120,
                "max_mp": 0,
                "max_stamina": 60,
                "combat_stats": {
                    "physical_attack": 32,
                    "physical_defense": 25,
                    "magic_attack": 0,
                    "magic_defense": 10,
                    "accuracy": 75,
                    "evasion": 5,
                    "critical_chance": 5,
                    "initiative": 10,
                },
                "resistances": {"poison": 100, "holy": -50},
                "behavior": {"skill": "BONE_CRUSH"},
                "reward_experience": 180,
                "reward_gold": 60,
                "loot_item_id": STONE_ID,
                "loot_chance_percent": 40,
                "escape_blocked": True,
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
                "id": WASP_ENCOUNTER_ID,
                "name": "Buzzing Shadows",
                "location_id": SYLVAN_BRANCH_ID,
                "monster_id": WASP_ID,
                "difficulty": "NORMAL",
                "enabled": True,
            },
            {
                "id": SKELETON_ENCOUNTER_ID,
                "name": "Guardian of the Path",
                "location_id": SYLVAN_BRANCH_ID,
                "monster_id": SKELETON_MONSTER_ID,
                "difficulty": "ELITE",
                "enabled": True,
            },
        ],
    )

    # 5. Add new Quests
    quests = sa.table(
        "quests",
        sa.column("id", sa.Uuid()),
        sa.column("title", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("location_id", sa.Uuid()),
        sa.column("giver_npc_id", sa.Uuid()),
        sa.column("faction_id", sa.Uuid()),
        sa.column("minimum_level", sa.SmallInteger()),
        sa.column("prerequisites", sa.JSON()),
        sa.column("rewards", sa.JSON()),
        sa.column("repeatable", sa.Boolean()),
    )
    op.bulk_insert(
        quests,
        [
            {
                "id": QUEST_IRON_ID,
                "title": "The Master's Iron",
                "description": "Blacksmith Hagar needs high-grade iron ore for a royal request.",
                "location_id": VALERIS_ID,
                "giver_npc_id": HAGAR_ID,
                "faction_id": None,
                "minimum_level": 3,
                "prerequisites": [],
                "rewards": {"experience": 350, "gold": 250, "reputation": 0},
                "repeatable": False,
            },
            {
                "id": QUEST_RECON_ID,
                "title": "Sylvan Reconnaissance",
                "description": "Scout Kael wants you to map the newly discovered Sylvan Branch trail.",
                "location_id": GREENWOOD_ID,
                "giver_npc_id": KAEL_ID,
                "faction_id": "72000000-0000-0000-0000-000000000001",
                "minimum_level": 2,
                "prerequisites": [],
                "rewards": {"experience": 250, "gold": 100, "reputation": 50},
                "repeatable": False,
            },
            {
                "id": QUEST_SIDE_ID,
                "title": "A Scout's Tool",
                "description": "Kael needs a sharpening stone to keep his daggers ready.",
                "location_id": GREENWOOD_ID,
                "giver_npc_id": KAEL_ID,
                "faction_id": None,
                "minimum_level": 1,
                "prerequisites": [],
                "rewards": {"experience": 100, "gold": 50, "reputation": 10},
                "repeatable": True,
            },
        ],
    )

    steps = sa.table(
        "quest_steps",
        sa.column("id", sa.Uuid()),
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
                "id": "76000000-0000-0000-0000-000000000006",
                "quest_id": QUEST_IRON_ID,
                "sequence": 0,
                "objective_type": "NPC_HELP",
                "target_id": HAGAR_ID,
                "description": "Speak with Hagar about the ore.",
                "required_count": 1,
            },
            {
                "id": "76000000-0000-0000-0000-000000000007",
                "quest_id": QUEST_RECON_ID,
                "sequence": 0,
                "objective_type": "LOCATION_DISCOVERY",
                "target_id": SYLVAN_BRANCH_ID,
                "description": "Reach the Sylvan Branch.",
                "required_count": 1,
            },
            {
                "id": "76000000-0000-0000-0000-000000000008",
                "quest_id": QUEST_SIDE_ID,
                "sequence": 0,
                "objective_type": "NPC_HELP",
                "target_id": KAEL_ID,
                "description": "Bring a sharpening stone to Kael.",
                "required_count": 1,
            },
        ],
    )


def downgrade() -> None:
    # Explicitly cast to UUID in SQL to avoid asyncpg type mismatch
    op.execute(
        sa.text(
            "DELETE FROM quest_steps WHERE quest_id IN (CAST(:q1 AS UUID), CAST(:q2 AS UUID), CAST(:q3 AS UUID))"
        ).bindparams(q1=QUEST_IRON_ID, q2=QUEST_RECON_ID, q3=QUEST_SIDE_ID)
    )
    op.execute(
        sa.text(
            "DELETE FROM quests WHERE id IN (CAST(:q1 AS UUID), CAST(:q2 AS UUID), CAST(:q3 AS UUID))"
        ).bindparams(q1=QUEST_IRON_ID, q2=QUEST_RECON_ID, q3=QUEST_SIDE_ID)
    )
    op.execute(
        sa.text(
            "DELETE FROM encounter_definitions WHERE id IN (CAST(:e1 AS UUID), CAST(:e2 AS UUID))"
        ).bindparams(e1=WASP_ENCOUNTER_ID, e2=SKELETON_ENCOUNTER_ID)
    )
    op.execute(
        sa.text("DELETE FROM monsters WHERE id IN (CAST(:m1 AS UUID), CAST(:m2 AS UUID))").bindparams(
            m1=WASP_ID, m2=SKELETON_MONSTER_ID
        )
    )
    op.execute(
        sa.text("DELETE FROM npcs WHERE id IN (CAST(:n1 AS UUID), CAST(:n2 AS UUID))").bindparams(
            n1=HAGAR_ID, n2=KAEL_ID
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM location_routes WHERE destination_location_id = CAST(:l1 AS UUID) OR origin_location_id = CAST(:l1 AS UUID)"
        ).bindparams(l1=SYLVAN_BRANCH_ID)
    )
    op.execute(
        sa.text("DELETE FROM locations WHERE id = CAST(:l1 AS UUID)").bindparams(
            l1=SYLVAN_BRANCH_ID
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM items WHERE id IN (CAST(:i1 AS UUID), CAST(:i2 AS UUID), CAST(:i3 AS UUID))"
        ).bindparams(i1=ORE_ID, i2=STONE_ID, i3=MAP_ID)
    )
