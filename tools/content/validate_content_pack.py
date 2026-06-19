import json
import sys
import os

try:
    from jsonschema import Draft7Validator, FormatChecker
except ImportError as exc:
    Draft7Validator = None
    FormatChecker = None
    JSONSCHEMA_IMPORT_ERROR = exc
else:
    JSONSCHEMA_IMPORT_ERROR = None

CONTENT_ID_FIELDS = {
    "npcs": "id",
    "locations": "id",
    "quests": "id",
    "enemies": "id",
    "items": "id",
    "shops": "id",
    "inns": "id",
    "dialogue_seeds": "id",
}


def _validate_schema(pack, schema_file: str) -> list[str]:
    if Draft7Validator is None or FormatChecker is None:
        return [
            f"jsonschema is required for content pack validation: {JSONSCHEMA_IMPORT_ERROR}"
        ]

    if not os.path.exists(schema_file):
        return [f"Schema file not found: {schema_file}"]

    with open(schema_file, "r") as f:
        schema = json.load(f)

    validator = Draft7Validator(schema, format_checker=FormatChecker())
    return [
        f"Schema validation error: {error.message} at {list(error.path)}"
        for error in sorted(
            validator.iter_errors(pack), key=lambda item: list(item.path)
        )
    ]


def _duplicate_content_id_errors(pack) -> list[str]:
    errors = []
    seen_ids = {}

    for collection_name, id_field in CONTENT_ID_FIELDS.items():
        for entry in pack.get(collection_name, []):
            content_id = entry.get(id_field)
            if not content_id:
                continue

            current_location = f"{collection_name}.{id_field}"
            previous_location = seen_ids.get(content_id)
            if previous_location is not None:
                errors.append(
                    f"Duplicate content id {content_id} in {current_location}; "
                    f"already used in {previous_location}"
                )
            else:
                seen_ids[content_id] = current_location

    return errors


def validate_pack(pack_path: str):
    pack_file = os.path.join(pack_path, "pack.json")
    if not os.path.exists(pack_file):
        print(f"Error: {pack_file} not found.")
        return False

    schema_file = os.path.join(
        os.path.dirname(__file__), "../../content/schemas/content_pack.schema.json"
    )

    with open(pack_file, "r") as f:
        try:
            pack = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return False

    errors = []

    # 1. Schema validation must fail closed when jsonschema is unavailable.
    errors.extend(_validate_schema(pack, schema_file))

    if errors:
        for err in errors:
            print(f"FAIL: {err}")
        return False

    # 2. Reject duplicate entity IDs before referential checks mask them.
    errors.extend(_duplicate_content_id_errors(pack))

    if errors:
        print(f"Validation failed for pack {pack['pack_id']}:")
        for err in errors:
            print(f"  - {err}")
        return False

    # 3. Collect IDs for referential integrity
    npc_ids = {npc["id"] for npc in pack.get("npcs", [])}
    location_ids = {loc["id"] for loc in pack.get("locations", [])}
    item_ids = {item["id"] for item in pack.get("items", [])}
    enemy_ids = {enemy["id"] for enemy in pack.get("enemies", [])}

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

    # 4. Referential Integrity Checks
    for npc in pack.get("npcs", []):
        if npc["home_location_id"] not in all_location_ids:
            errors.append(
                f"NPC {npc['name']} ({npc['id']}) references unknown location {npc['home_location_id']}"
            )

    for quest in pack.get("quests", []):
        if quest["giver_npc_id"] not in all_npc_ids:
            errors.append(
                f"Quest {quest['title']} ({quest['id']}) references unknown giver {quest['giver_npc_id']}"
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
                    f"Quest {quest['title']} step {i} references unknown location {target_id}"
                )
            elif obj_type == "NPC_HELP" and target_id not in all_npc_ids:
                errors.append(
                    f"Quest {quest['title']} step {i} references unknown NPC {target_id}"
                )
            elif obj_type == "DEFEAT" and target_id not in enemy_ids:
                errors.append(
                    f"Quest {quest['title']} step {i} references unknown enemy {target_id}"
                )

    for shop in pack.get("shops", []):
        if shop["owner_npc_id"] not in all_npc_ids:
            errors.append(
                f"Shop {shop['name']} references unknown owner {shop['owner_npc_id']}"
            )
        for item_ref in shop.get("items", []):
            if item_ref["item_id"] not in item_ids:
                errors.append(
                    f"Shop {shop['name']} references unknown item {item_ref['item_id']}"
                )

    for inn in pack.get("inns", []):
        if inn["location_id"] not in all_location_ids:
            errors.append(
                f"Inn {inn['name']} references unknown location {inn['location_id']}"
            )

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
