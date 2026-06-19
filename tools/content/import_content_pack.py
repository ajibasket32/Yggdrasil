import argparse
import json
import os
import sys
from datetime import UTC, datetime


REQUIRED_REPORTS = {
    "validation_report.json": "PASS",
    "asset_resolution_report.json": "PASS",
    "simulation_report.json": "PASS",
}


def _load_json(path: str) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _check_reports(pack_path: str) -> list[str]:
    errors: list[str] = []
    for filename, required_status in REQUIRED_REPORTS.items():
        path = os.path.join(pack_path, filename)
        if not os.path.exists(path):
            errors.append(f"Missing required report: {filename}")
            continue
        report = _load_json(path)
        if report.get("status") != required_status:
            errors.append(
                f"{filename} status is {report.get('status')}, "
                f"expected {required_status}"
            )
    return errors


def import_pack(pack_path: str, apply: bool = False, approve: bool = False) -> bool:
    pack_file = os.path.join(pack_path, "pack.json")
    errors = _check_reports(pack_path)
    pack: dict[str, object] = {}
    if not os.path.exists(pack_file):
        errors.append("Missing required pack.json")
    else:
        pack = _load_json(pack_file)

    if apply and not approve:
        errors.append("Apply mode requires --approve.")
    if apply and pack.get("validation_status") not in {"validated", "approved"}:
        errors.append("Apply mode requires pack validation_status to be validated or approved.")
    if apply:
        errors.append("Apply mode is reserved for a future backend import service.")

    report = {
        "tool": "import_content_pack",
        "checked_at": datetime.now(UTC).isoformat(),
        "pack_id": pack.get("pack_id"),
        "mode": "apply" if apply else "dry-run",
        "status": "PASS" if not errors else "FAIL",
        "mutated_database": False,
        "errors": errors,
        "would_import": {
            "locations": len(pack.get("locations", [])),
            "npcs": len(pack.get("npcs", [])),
            "items": len(pack.get("items", [])),
            "quests": len(pack.get("quests", [])),
            "shops": len(pack.get("shops", [])),
            "inns": len(pack.get("inns", [])),
        },
    }
    with open(os.path.join(pack_path, "import_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if errors:
        print("Content import refused:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("Content import dry-run PASSED. No database changes were made.")
    for name, count in report["would_import"].items():
        print(f"  - {name}: {count}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate content pack import readiness.")
    parser.add_argument("pack_path", help="Path to the content pack directory")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run only (default)")
    parser.add_argument("--apply", action="store_true", help="Attempt an approved import")
    parser.add_argument("--approve", action="store_true", help="Explicitly approve apply mode")
    args = parser.parse_args()
    sys.exit(0 if import_pack(args.pack_path, apply=args.apply, approve=args.approve) else 1)
