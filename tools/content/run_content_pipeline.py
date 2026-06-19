import argparse
import json
import os
import sys
from datetime import UTC, datetime

from content_ai_orchestrator import orchestrate_ai
from generate_content_pack import generate_pack
from resolve_asset_manifest import resolve_assets
from simulate_content_pack import simulate_pack
from validate_content_pack import validate_pack


def run_pipeline(seed: int, theme: str, out_dir: str, ai_repair: bool = False) -> bool:
    os.makedirs(out_dir, exist_ok=True)
    steps: list[dict[str, object]] = []

    generate_pack(seed, theme, out_dir)
    steps.append({"step": "generate", "status": "PASS"})

    validation_ok = validate_pack(out_dir)
    steps.append({"step": "validate", "status": "PASS" if validation_ok else "FAIL"})

    asset_ok = resolve_assets(out_dir, download=False)
    steps.append({"step": "resolve_assets", "status": "PASS" if asset_ok else "FAIL"})

    simulation_ok = simulate_pack(out_dir)
    steps.append({"step": "simulate", "status": "PASS" if simulation_ok else "FAIL"})

    ai_ok = True
    if ai_repair:
        ai_ok = orchestrate_ai(out_dir, repair=True, allow_cloud_ai=False, apply=False)
        steps.append({"step": "ai_repair_analyze", "status": "PASS" if ai_ok else "FAIL"})

    success = validation_ok and asset_ok and simulation_ok and ai_ok
    report = {
        "tool": "run_content_pipeline",
        "checked_at": datetime.now(UTC).isoformat(),
        "seed": seed,
        "theme": theme,
        "out_dir": out_dir,
        "status": "PASS" if success else "FAIL",
        "internet_required": False,
        "cloud_ai_required": False,
        "auto_imported": False,
        "steps": steps,
    }
    with open(os.path.join(out_dir, "pipeline_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Pipeline report written to {os.path.join(out_dir, 'pipeline_report.json')}")
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the safe deterministic content pipeline.")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--theme", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--ai-repair", action="store_true")
    args = parser.parse_args()
    sys.exit(0 if run_pipeline(args.seed, args.theme, args.out, args.ai_repair) else 1)
