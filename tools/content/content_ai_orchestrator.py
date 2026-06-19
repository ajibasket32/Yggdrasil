import json
import sys
import os
import hashlib
from typing import Dict, Any, List

def orchestrate_ai(pack_path: str, repair: bool = False):
    pack_file = os.path.join(pack_path, "pack.json")
    if not os.path.exists(pack_file):
        print(f"Error: {pack_file} not found.")
        return False

    api_key = os.getenv("AI_API_KEY")

    # Generate cache key from pack content
    with open(pack_file, "rb") as f:
        pack_hash = hashlib.sha256(f.read()).hexdigest()

    suggestion_file = os.path.join(pack_path, "ai_repair_suggestion.json")

    if not api_key:
        print("AI_API_KEY not found. Providing deterministic fallback advice.")
        fallback_suggestion = {
            "pack_id": "unknown",
            "hash": pack_hash,
            "suggestions": [
                "Ensure all UUIDs are valid and unique.",
                "Verify that giver_npc_id exists in the npcs array.",
                "Check that all objective target_ids reference existing items or locations.",
                "Ensure license metadata is present in assets.json."
            ],
            "status": "deterministic_fallback"
        }
        with open(suggestion_file, "w") as f:
            json.dump(fallback_suggestion, f, indent=2)
        print(f"Deterministic fallback advice written to {suggestion_file}")
        return True

    print(f"AI Orchestrator running for {pack_path} (Repair: {repair})")
    # In a real system, this would call the AI adapters with validation errors
    # and provide a JSON patch or specific repair instructions.

    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Optional AI-light content orchestrator.")
    parser.add_argument("--pack", required=True, help="Path to the content pack directory")
    parser.add_argument("--repair", action="store_true", help="Request AI to suggest repairs for validation errors")

    args = parser.parse_args()
    success = orchestrate_ai(args.pack, args.repair)
    sys.exit(0 if success else 1)
