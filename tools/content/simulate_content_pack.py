import json
import os
import sys
from datetime import UTC, datetime


def simulate_pack(pack_path: str) -> bool:
    pack_file = os.path.join(pack_path, "pack.json")
    report_file = os.path.join(pack_path, "simulation_report.json")
    errors: list[str] = []

    if not os.path.exists(pack_file):
        errors.append(f"{pack_file} not found.")
        pack: dict[str, object] = {}
    else:
        with open(pack_file, "r", encoding="utf-8") as f:
            pack = json.load(f)

    for quest in pack.get("quests", []):
        rewards = quest.get("rewards", {})
        if int(rewards.get("experience", 0)) < 0:
            errors.append(f"Quest {quest.get('id')} has negative experience reward.")
        if int(rewards.get("gold", 0)) < 0:
            errors.append(f"Quest {quest.get('id')} has negative gold reward.")

    for shop in pack.get("shops", []):
        for item in shop.get("items", []):
            if int(item.get("price", 0)) < 0:
                errors.append(f"Shop {shop.get('id')} has negative item price.")

    for inn in pack.get("inns", []):
        if int(inn.get("rest_cost", 0)) < 0:
            errors.append(f"Inn {inn.get('id')} has negative rest cost.")

    report = {
        "tool": "simulate_content_pack",
        "checked_at": datetime.now(UTC).isoformat(),
        "pack_id": pack.get("pack_id"),
        "status": "PASS" if not errors else "FAIL",
        "mutated_game_state": False,
        "checks": [
            "quest_rewards_non_negative",
            "shop_prices_non_negative",
            "inn_costs_non_negative",
            "dry_run_only",
        ],
        "errors": errors,
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if errors:
        print(f"Simulation failed for {pack_path}:")
        for error in errors:
            print(f"  - {error}")
        return False

    print(f"Simulation PASSED for {pack_path}")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dry-run simulate a content pack.")
    parser.add_argument("pack_path", help="Path to the content pack directory")
    args = parser.parse_args()
    sys.exit(0 if simulate_pack(args.pack_path) else 1)
