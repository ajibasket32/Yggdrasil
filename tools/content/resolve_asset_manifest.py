import json
import sys
import os
from datetime import UTC, datetime

ALLOWED_DOMAINS = [
    "opengameart.org",
    "kenney.nl",
    "raw.githubusercontent.com/KenneyNL"
]

def resolve_assets(pack_path: str, download: bool = False) -> bool:
    manifest_file = os.path.join(pack_path, "assets.json")
    if not os.path.exists(manifest_file):
        print(f"Error: {manifest_file} not found.")
        return False

    with open(manifest_file, "r", encoding="utf-8") as f:
        try:
            manifest = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return False

    report = {
        "tool": "resolve_asset_manifest",
        "checked_at": datetime.now(UTC).isoformat(),
        "pack_id": manifest.get("pack_id"),
        "status": "PASS",
        "download_requested": download,
        "resolution_results": []
    }

    all_ok = True
    for asset in manifest.get("assets", []):
        result = {
            "asset_id": asset["asset_id"],
            "status": asset["status"],
            "notes": []
        }

        # Check license
        if "license" not in asset or not asset["license"]:
            result["status"] = "blocked"
            result["notes"].append("Missing license metadata.")
            all_ok = False
        elif asset["license"] not in ["CC0", "Public Domain", "Kenney"]:
            result["status"] = "needs_review"
            result["notes"].append(f"Uncommon license: {asset['license']}")

        # Check local fallback
        fallback = asset.get("preferred_fallback")
        if fallback:
            # Check if fallback exists relative to repo root
            if os.path.exists(fallback):
                result["notes"].append(f"Local fallback found: {fallback}")
            else:
                result["notes"].append(f"Local fallback missing: {fallback}")
                if asset["status"] == "local":
                    result["status"] = "missing"
                    all_ok = False

        # Check remote URL
        remote_url = asset.get("remote_url")
        if remote_url:
            domain_ok = any(domain in remote_url for domain in ALLOWED_DOMAINS)
            if not domain_ok:
                result["status"] = "blocked"
                result["notes"].append(f"Domain not in allowlist: {remote_url}")
                all_ok = False

            if download and result["status"] not in ["blocked", "missing"]:
                # Real download would happen here
                result["notes"].append(f"Download simulated for: {remote_url}")
                result["status"] = "downloaded"

        report["resolution_results"].append(result)

    report_file = os.path.join(pack_path, "asset_resolution_report.json")
    report["status"] = "PASS" if all_ok else "FAIL"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Asset resolution report written to {report_file}")
    for res in report["resolution_results"]:
        print(f"  - {res['asset_id']}: {res['status']} ({', '.join(res['notes'])})")

    return all_ok

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Resolve asset manifest for a content pack.")
    parser.add_argument("pack_path", help="Path to the content pack directory")
    parser.add_argument("--download", action="store_true", help="Attempt to download remote assets")

    args = parser.parse_args()
    success = resolve_assets(args.pack_path, args.download)
    sys.exit(0 if success else 1)
