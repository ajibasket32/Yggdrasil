import json
import os
import sys
from datetime import UTC, datetime

try:
    from jsonschema import ValidationError, validate
except ImportError:
    validate = None

ALLOWED_REGION_TYPES = {
    "safe_hub",
    "route",
    "town_interior",
    "shop_interior",
    "inn_interior",
    "quest_area",
    "combat_region",
    "dungeon_route",
    "forest_route",
}

ALLOWED_MAP_TEMPLATES = {
    "city_hub",
    "forest_route",
    "countryside_route",
    "shop_interior",
    "inn_interior",
    "dungeon_route",
    "combat_clearing",
}

BASE_MUSIC_KEYS = {
    "title_theme",
    "valeris_city",
    "valeris_outskirts",
    "sylvan_branch",
    "battle_theme",
}


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


def _load_asset_manifest(pack_path: str) -> tuple[dict[str, dict], list[str]]:
    manifest_file = os.path.join(pack_path, "assets.json")
    if not os.path.exists(manifest_file):
        return {}, ["Missing required asset manifest: assets.json"]

    with open(manifest_file, encoding="utf-8") as f:
        try:
            manifest = json.load(f)
        except json.JSONDecodeError as e:
            return {}, [f"Error decoding asset manifest: {e}"]

    errors = []
    assets = {}
    for asset in manifest.get("assets", []):
        asset_id = asset.get("asset_id")
        if not asset_id:
            errors.append("Asset is missing asset_id")
            continue
        assets[asset_id] = asset
        if not asset.get("source_name"):
            errors.append(f"Asset {asset_id} is missing source_name")
        if not asset.get("license"):
            errors.append(f"Asset {asset_id} is missing license")
    return assets, errors


def _validate_location_maps(
    locations: list[dict],
    asset_ids: set[str],
    music_keys: set[str],
) -> list[str]:
    errors = []
    layout_hashes = set()

    for location in locations:
        name = location.get("name", location.get("id", "unknown"))
        if location.get("region_type") not in ALLOWED_REGION_TYPES:
            errors.append(f"Location {name} has invalid region_type")
        if location.get("map_template") not in ALLOWED_MAP_TEMPLATES:
            errors.append(f"Location {name} has invalid map_template")
        if not location.get("landmarks"):
            errors.append(f"Location {name} has no landmarks")
        if not location.get("theme"):
            errors.append(f"Location {name} is missing map theme")
        layout_hash = location.get("layout_hash")
        if not layout_hash:
            errors.append(f"Location {name} is missing layout_hash")
        elif layout_hash in layout_hashes:
            errors.append(f"Location {name} reuses layout_hash {layout_hash}")
        else:
            layout_hashes.add(layout_hash)

        music_key = location.get("music_key")
        if music_key not in music_keys:
            errors.append(
                f"Location {name} references unavailable music key {music_key}"
            )

        for asset_ref in location.get("asset_manifest", []):
            if asset_ref not in asset_ids and asset_ref not in BASE_MUSIC_KEYS:
                errors.append(f"Location {name} references unknown asset {asset_ref}")

    return errors


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

    with open(pack_file, encoding="utf-8") as f:
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
        with open(schema_file, encoding="utf-8") as f:
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

    if pack.get("validation_status") == "validated":
        errors.append("Content pack cannot self-mark validation_status as validated")

    assets, asset_errors = _load_asset_manifest(pack_path)
    errors.extend(asset_errors)
    music_keys = BASE_MUSIC_KEYS.union(
        {
            asset_id
            for asset_id, asset in assets.items()
            if asset.get("type") == "sound" and asset.get("status") == "local"
        }
    )

    # 2. Collect IDs for referential integrity
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
    locations_by_id = {loc["id"]: loc for loc in pack.get("locations", [])}

    errors.extend(
        _validate_location_maps(
            pack.get("locations", []),
            set(assets.keys()),
            music_keys,
        )
    )

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
                errors.append(
                    f"Quest {quest['title']} step {i} references unknown NPC {target_id}"
                )
            elif obj_type == "DEFEAT" and target_id not in enemy_ids:
                errors.append(
                    f"Quest {quest['title']} step {i} references unknown enemy {target_id}"
                )
            zone_id = step.get("map_zone_id")
            if zone_id:
                target_location = locations_by_id.get(target_id)
                zones = set((target_location or {}).get("interaction_zones", []))
                if zone_id not in zones:
                    errors.append(
                        f"Quest {quest['title']} step {i} references invalid map zone {zone_id}"
                    )

    for shop in pack.get("shops", []):
        if shop["owner_npc_id"] not in all_npc_ids:
            errors.append(
                f"Shop {shop['name']} references unknown owner {shop['owner_npc_id']}"
            )
        owner = next(
            (npc for npc in pack.get("npcs", []) if npc["id"] == shop["owner_npc_id"]),
            None,
        )
        owner_location = (
            locations_by_id.get(owner["home_location_id"]) if owner else None
        )
        if owner_location and owner_location.get("map_template") not in {
            "city_hub",
            "shop_interior",
        }:
            errors.append(
                f"Shop {shop['name']} is not assigned to a coherent shop location"
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
        inn_location = locations_by_id.get(inn["location_id"])
        if inn_location and inn_location.get("map_template") not in {
            "city_hub",
            "inn_interior",
            "forest_route",
        }:
            errors.append(
                f"Inn {inn['name']} is not assigned to a coherent inn location"
            )

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
