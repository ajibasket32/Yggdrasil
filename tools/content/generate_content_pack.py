import json
import sys
import os
import random
import uuid
from typing import Dict, Any, List

def generate_pack(seed: int, theme: str, out_dir: str):
    random.seed(seed)
    os.makedirs(out_dir, exist_ok=True)

    pack_id = f"generated_{theme}_{seed}"

    # Deterministic UUID generation from seed
    def seeded_uuid(name: str) -> str:
        u = uuid.UUID(int=random.getrandbits(128))
        return str(u)

    location_id = seeded_uuid("location")
    npc_id = seeded_uuid("npc")
    item_id = seeded_uuid("item")
    quest_id = seeded_uuid("quest")

    pack = {
        "pack_id": pack_id,
        "version": "1.0.0",
        "generated_by": "seeded_generator",
        "seed": seed,
        "theme": theme,
        "locations": [
            {
                "id": location_id,
                "name": f"{theme.capitalize()} Outpost",
                "region": "Valeria",
                "description": f"A small outpost themed around {theme}."
            }
        ],
        "npcs": [
            {
                "id": npc_id,
                "name": f"Guide {random.choice(['Aria', 'Bryn', 'Cael', 'Dara'])}",
                "role": "GUIDE",
                "home_location_id": location_id,
                "personality": { "archetype": "helpful" }
            }
        ],
        "items": [
            {
                "id": item_id,
                "name": f"{theme.capitalize()} Token",
                "type": "QUEST_ITEM",
                "base_value": 0
            }
        ],
        "quests": [
            {
                "id": quest_id,
                "title": f"The {theme.capitalize()} Trial",
                "description": f"Prove your worth in the {theme} lands.",
                "giver_npc_id": npc_id,
                "steps": [
                    {
                        "objective_type": "FETCH",
                        "target_id": item_id,
                        "count": 1,
                        "description": f"Retrieve the {theme.capitalize()} Token."
                    }
                ],
                "rewards": {
                    "experience": 200,
                    "gold": 100
                }
            }
        ],
        "validation_status": "pending"
    }

    pack_file = os.path.join(out_dir, "pack.json")
    with open(pack_file, "w") as f:
        json.dump(pack, f, indent=2)

    assets = {
        "pack_id": pack_id,
        "assets": [
            {
                "asset_id": f"npc_{npc_id}_sprite",
                "type": "sprite",
                "license": "CC0",
                "status": "local",
                "preferred_fallback": "assets/ui/portraits/placeholder.png"
            }
        ]
    }

    assets_file = os.path.join(out_dir, "assets.json")
    with open(assets_file, "w") as f:
        json.dump(assets, f, indent=2)

    print(f"Content pack generated at {out_dir}")
    return pack

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate a seeded content pack.")
    parser.add_argument("--seed", type=int, required=True, help="Seed for generation")
    parser.add_argument("--theme", type=str, required=True, help="Theme for the pack")
    parser.add_argument("--out", type=str, required=True, help="Output directory")

    args = parser.parse_args()
    generate_pack(args.seed, args.theme, args.out)
