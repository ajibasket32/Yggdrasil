import json
import sys
import os
import hashlib
from datetime import UTC, datetime


def _load_pack_summary(pack_file: str) -> dict[str, object]:
    with open(pack_file, "r", encoding="utf-8") as f:
        pack = json.load(f)
    return {
        "pack_id": pack.get("pack_id"),
        "counts": {
            "locations": len(pack.get("locations", [])),
            "npcs": len(pack.get("npcs", [])),
            "items": len(pack.get("items", [])),
            "quests": len(pack.get("quests", [])),
            "enemies": len(pack.get("enemies", [])),
            "shops": len(pack.get("shops", [])),
            "inns": len(pack.get("inns", [])),
        },
    }


def orchestrate_ai(
    pack_path: str,
    repair: bool = False,
    allow_cloud_ai: bool = False,
    apply: bool = False,
) -> bool:
    pack_file = os.path.join(pack_path, "pack.json")
    if not os.path.exists(pack_file):
        print(f"Error: {pack_file} not found.")
        return False

    # Generate cache key from pack content
    with open(pack_file, "rb") as f:
        pack_hash = hashlib.sha256(f.read()).hexdigest()

    suggestion_file = os.path.join(pack_path, "ai_repair_suggestion.json")
    if os.path.exists(suggestion_file):
        with open(suggestion_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
        if (
            cached.get("hash") == pack_hash
            and cached.get("tool") == "content_ai_orchestrator"
        ):
            print(f"AI-light cache hit for {pack_hash}.")
            return True

    if not allow_cloud_ai:
        print("Cloud AI disabled. Providing deterministic fallback advice.")
        summary = _load_pack_summary(pack_file)
        fallback_suggestion = {
            "tool": "content_ai_orchestrator",
            "checked_at": datetime.now(UTC).isoformat(),
            "pack_id": summary["pack_id"],
            "hash": pack_hash,
            "repair_requested": repair,
            "apply_requested": apply,
            "cloud_ai_used": False,
            "mutation_applied": False,
            "context": summary,
            "suggestions": [
                "Ensure all UUIDs are valid and unique.",
                "Verify that giver_npc_id exists in the npcs array.",
                "Check that all objective target_ids reference existing items or locations.",
                "Ensure license metadata is present in assets.json."
            ],
            "status": "deterministic_fallback",
            "usage": {"provider_calls": 0, "tokens": 0},
        }
        with open(suggestion_file, "w", encoding="utf-8") as f:
            json.dump(fallback_suggestion, f, indent=2)
        print(f"Deterministic fallback advice written to {suggestion_file}")
        return True

    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        print("AI_API_KEY not found. Cloud AI was explicitly allowed but is unavailable.")
        return False

    print(f"AI Orchestrator running for {pack_path} (Repair: {repair})")
    # In a real system, this would call the AI adapters with validation errors
    # and provide a JSON patch or specific repair instructions.

    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Optional AI-light content orchestrator.")
    parser.add_argument("--pack", required=True, help="Path to the content pack directory")
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Request AI to suggest repairs for validation errors",
    )
    parser.add_argument(
        "--allow-cloud-ai",
        action="store_true",
        help="Allow configured cloud AI use",
    )
    parser.add_argument("--apply", action="store_true", help="Allow applying a validated AI patch")

    args = parser.parse_args()
    success = orchestrate_ai(args.pack, args.repair, args.allow_cloud_ai, args.apply)
    sys.exit(0 if success else 1)
