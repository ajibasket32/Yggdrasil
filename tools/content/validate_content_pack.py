import os
import json
import sys
from datetime import UTC, datetime

try:
    from jsonschema import validate, ValidationError
except ImportError:
    validate = None

MUSIC_KEYS = {"title", "city", "interior", "outskirts", "forest", "battle"}
COMBAT_BACKGROUND_KEYS = {"city_gate", "forest"}


def _write_report(pack_path: str, pack_id: str | None, errors: list[str]) -> None:
    report = {
        "tool": "validate_content_pack",
        "checked_at": datetime.now(UTC).isoformat(),
        "pack_id": pack_id,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    report_file = os.path.join(pack_path, "validation_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def validate_pack(pack_path: str) -> bool:
    pack_file = os.path.join(pack_path, "pack.json")
    if not os.path.exists(pack_file):
        error = f"{pack_file} not found."
        print(f"Error: {error}")
        _write_report(pack_path, None, [error])
        return False

    schema_file = os.path.join(
        os.path.dirname(__file__),
        "../../content/schemas/content_pack.schema.json",
    )

    with open(pack_file, "r", encoding="utf-8") as f:
        try:
            pack = json.load(f)
        except json.JSONDecodeError as e:
            error = f"Error decoding JSON: {e}"
            print(error)
            _write_report(pack_path, None, [error])
            return False

    errors = []

    # 1. Schema validation using jsonschema if available
    if validate and os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
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
        _write_report(pack_path, pack.get("pack_id"), errors)
        return False

    # 2. Collect IDs for referential integrity
    npc_ids = {npc["id"] for npc in pack.get("npcs", [])}
    location_ids = {loc["id"] for loc in pack.get("locations", [])}
    item_ids = {item["id"] for item in pack.get("items", [])}
    enemy_ids = {enemy["id"] for enemy in pack.get("enemies", [])}
    locations_by_id = {loc["id"]: loc for loc in pack.get("locations", [])}

    # Base game IDs for cross-pack/base-game references
    base_npc_ids = [
        "74000000-0000-0000-0000-000000000002",
        "74000000-0000-0000-0000-000000000006",
        "74000000-0000-0000-0000-000000000007",
    ]
    base_location_ids = [
        "56000000-0000-0000-0000-000000000002",
        "56000000-0000-0000-0000-000000000005",
    ]

    all_npc_ids = npc_ids.union(set(base_npc_ids))
    all_location_ids = location_ids.union(set(base_location_ids))

    layout_hashes: dict[str, str] = {}
    for loc in pack.get("locations", []):
        loc_id = loc["id"]
        if not loc.get("purpose"):
            errors.append(f"Location {loc['name']} ({loc_id}) is missing a clear purpose")
        layout_hash = loc.get("layout_hash")
        if layout_hash in layout_hashes:
            errors.append(
                f"Locations {layout_hashes[layout_hash]} and {loc_id} reuse layout_hash "
                f"{layout_hash}"
            )
        layout_hashes[layout_hash] = loc_id
        if loc.get("music_key") not in MUSIC_KEYS:
            errors.append(f"Location {loc['name']} uses unknown music key {loc.get('music_key')}")
        if loc.get("combat_background_key") not in COMBAT_BACKGROUND_KEYS:
            errors.append(
                f"Location {loc['name']} uses unknown combat background "
                f"{loc.get('combat_background_key')}"
            )
        if not loc.get("asset_manifest_ref"):
            errors.append(f"Location {loc['name']} is missing asset provenance")

    # 3. Referential Integrity Checks
    for npc in pack.get("npcs", []):
        if npc["home_location_id"] not in all_location_ids:
            errors.append(
                f"NPC {npc['name']} ({npc['id']}) references unknown "
                f"location {npc['home_location_id']}"
            )

    for quest in pack.get("quests", []):
        if quest["giver_npc_id"] not in all_npc_ids:
            errors.append(
                f"Quest {quest['title']} ({quest['id']}) references unknown "
                f"giver {quest['giver_npc_id']}"
            )

        for i, step in enumerate(quest.get("steps", [])):
            target_id = step["target_id"]
            obj_type = step["objective_type"]

            if obj_type == "FETCH" and target_id not in item_ids:
                errors.append(
                    f"Quest {quest['title']} step {i} references unknown item {target_id}"
                )
            elif obj_type == "SCOUT" and target_id not in all_location_ids:
                errors.append(
                    f"Quest {quest['title']} step {i} references unknown "
                    f"location {target_id}"
                )
            elif obj_type == "NPC_HELP" and target_id not in all_npc_ids:
                errors.append(f"Quest {quest['title']} step {i} references unknown NPC {target_id}")
            elif obj_type == "DEFEAT" and target_id not in enemy_ids:
                errors.append(
                    f"Quest {quest['title']} step {i} references unknown enemy {target_id}"
                )

    for shop in pack.get("shops", []):
        if shop["owner_npc_id"] not in all_npc_ids:
            errors.append(f"Shop {shop['name']} references unknown owner {shop['owner_npc_id']}")
        shop_location_id = shop.get("location_id")
        if shop_location_id:
            location = locations_by_id.get(shop_location_id)
            if location and location.get("map_template") != "interior":
                errors.append(f"Shop {shop['name']} must use an interior location template")
        for item_ref in shop.get("items", []):
            if item_ref["item_id"] not in item_ids:
                errors.append(f"Shop {shop['name']} references unknown item {item_ref['item_id']}")

    for inn in pack.get("inns", []):
        if inn["location_id"] not in all_location_ids:
            errors.append(f"Inn {inn['name']} references unknown location {inn['location_id']}")
        location = locations_by_id.get(inn["location_id"])
        if location and location.get("map_template") != "interior":
            errors.append(f"Inn {inn['name']} must use an interior location template")

    if errors:
        print(f"Validation failed for pack {pack['pack_id']}:")
        for err in errors:
            print(f"  - {err}")
        _write_report(pack_path, pack.get("pack_id"), errors)
        return False

    print(f"Validation PASSED for pack {pack['pack_id']}")
    _write_report(pack_path, pack.get("pack_id"), [])
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_content_pack.py <pack_directory>")
        sys.exit(1)

    success = validate_pack(sys.argv[1])
    sys.exit(0 if success else 1)
