import json
import sys
import os
from uuid import UUID
from typing import Dict, Any, List
try:
    from jsonschema import validate, ValidationError
except ImportError:
    validate = None

def validate_pack(pack_path: str):
    pack_file = os.path.join(pack_path, "pack.json")
    if not os.path.exists(pack_file):
        print(f"Error: {pack_file} not found.")
        return False

    schema_file = os.path.join(os.path.dirname(__file__), "../../content/schemas/content_pack.schema.json")

    with open(pack_file, "r") as f:
        try:
            pack = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return False

    errors = []

    # 1. Schema validation using jsonschema if available
    if validate and os.path.exists(schema_file):
        with open(schema_file, "r") as f:
            schema = json.load(f)
        try:
            validate(instance=pack, schema=schema)
        except ValidationError as e:
            errors.append(f"Schema validation error: {e.message} at {list(e.path)}")
    else:
        # Fallback to manual basic checks if jsonschema is missing
        required_root = ["pack_id", "version", "npcs", "locations", "quests", "items"]
        for field in required_root:
            if field not in pack:
                errors.append(f"Missing required root field: {field}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}")
        return False

    # 2. Collect IDs for referential integrity
    npc_ids = {npc["id"] for npc in pack.get("npcs", [])}
    location_ids = {loc["id"] for loc in pack.get("locations", [])}
    item_ids = {item["id"] for item in pack.get("items", [])}
    enemy_ids = {enemy["id"] for enemy in pack.get("enemies", [])}

    # Base game IDs for cross-pack/base-game references
    base_npc_ids = ["74000000-0000-0000-0000-000000000002", "74000000-0000-0000-0000-000000000006", "74000000-0000-0000-0000-000000000007"]
    base_location_ids = ["56000000-0000-0000-0000-000000000002", "56000000-0000-0000-0000-000000000005"]

    all_npc_ids = npc_ids.union(set(base_npc_ids))
    all_location_ids = location_ids.union(set(base_location_ids))

    # 3. Referential Integrity Checks
    for npc in pack.get("npcs", []):
        if npc["home_location_id"] not in all_location_ids:
            errors.append(f"NPC {npc['name']} ({npc['id']}) references unknown location {npc['home_location_id']}")

    for quest in pack.get("quests", []):
        if quest["giver_npc_id"] not in all_npc_ids:
            errors.append(f"Quest {quest['title']} ({quest['id']}) references unknown giver {quest['giver_npc_id']}")

        for i, step in enumerate(quest.get("steps", [])):
            target_id = step["target_id"]
            obj_type = step["objective_type"]

            if obj_type == "FETCH" and target_id not in item_ids:
                errors.append(f"Quest {quest['title']} step {i} references unknown item {target_id}")
            elif obj_type == "SCOUT" and target_id not in all_location_ids:
                errors.append(f"Quest {quest['title']} step {i} references unknown location {target_id}")
            elif obj_type == "NPC_HELP" and target_id not in all_npc_ids:
                errors.append(f"Quest {quest['title']} step {i} references unknown NPC {target_id}")
            elif obj_type == "DEFEAT" and target_id not in enemy_ids:
                errors.append(f"Quest {quest['title']} step {i} references unknown enemy {target_id}")

    for shop in pack.get("shops", []):
        if shop["owner_npc_id"] not in all_npc_ids:
            errors.append(f"Shop {shop['name']} references unknown owner {shop['owner_npc_id']}")
        for item_ref in shop.get("items", []):
            if item_ref["item_id"] not in item_ids:
                errors.append(f"Shop {shop['name']} references unknown item {item_ref['item_id']}")

    for inn in pack.get("inns", []):
        if inn["location_id"] not in all_location_ids:
            errors.append(f"Inn {inn['name']} references unknown location {inn['location_id']}")

    if errors:
        print(f"Validation failed for pack {pack['pack_id']}:")
        for err in errors:
            print(f"  - {err}")
        return False

    print(f"Validation PASSED for pack {pack['pack_id']}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_content_pack.py <pack_directory>")
        sys.exit(1)

    success = validate_pack(sys.argv[1])
    sys.exit(0 if success else 1)
