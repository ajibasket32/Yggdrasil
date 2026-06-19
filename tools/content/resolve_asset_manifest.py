import json
import sys
import os
from urllib.parse import urlparse

ALLOWED_DOMAINS = [
    "opengameart.org",
    "kenney.nl",
    "raw.githubusercontent.com",
]

ALLOWED_GITHUB_PATH_PREFIXES = [
    "/KenneyNL/",
]


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _is_local_file_path(path: str) -> bool:
    parsed = urlparse(path)
    if parsed.scheme or parsed.netloc:
        return False

    if os.path.isabs(path):
        candidate = path
    else:
        candidate = os.path.join(_repo_root(), path)

    return os.path.isfile(candidate)


def _is_allowed_remote_url(remote_url: str) -> bool:
    parsed = urlparse(remote_url)
    hostname = parsed.hostname
    if parsed.scheme not in {"http", "https"} or hostname is None:
        return False

    normalized_hostname = hostname.lower()
    if normalized_hostname not in ALLOWED_DOMAINS:
        return False

    if normalized_hostname == "raw.githubusercontent.com":
        return any(
            parsed.path.startswith(prefix) for prefix in ALLOWED_GITHUB_PATH_PREFIXES
        )

    return True


def resolve_assets(pack_path: str, download: bool = False):
    manifest_file = os.path.join(pack_path, "assets.json")
    if not os.path.exists(manifest_file):
        print(f"Error: {manifest_file} not found.")
        return False

    with open(manifest_file, "r") as f:
        try:
            manifest = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return False

    report = {"pack_id": manifest.get("pack_id"), "resolution_results": []}

    all_ok = True
    for asset in manifest.get("assets", []):
        result = {"asset_id": asset["asset_id"], "status": asset["status"], "notes": []}

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
            if _is_local_file_path(fallback):
                result["notes"].append(f"Local fallback found: {fallback}")
            else:
                result["notes"].append(f"Local fallback missing: {fallback}")
                if asset["status"] == "local":
                    result["status"] = "missing"
                    all_ok = False
        elif asset["status"] == "local":
            result["status"] = "missing"
            result["notes"].append(
                "Local assets require preferred_fallback pointing to an existing file."
            )
            all_ok = False

        # Check remote URL
        remote_url = asset.get("remote_url")
        if remote_url:
            if not _is_allowed_remote_url(remote_url):
                result["status"] = "blocked"
                result["notes"].append(f"Domain not in allowlist: {remote_url}")
                all_ok = False

            if download and result["status"] not in ["blocked", "missing"]:
                # Real download would happen here
                result["notes"].append(f"Download simulated for: {remote_url}")
                result["status"] = "downloaded"

        report["resolution_results"].append(result)

    report_file = os.path.join(pack_path, "asset_resolution_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Asset resolution report written to {report_file}")
    for res in report["resolution_results"]:
        print(f"  - {res['asset_id']}: {res['status']} ({', '.join(res['notes'])})")

    return all_ok


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Resolve asset manifest for a content pack."
    )
    parser.add_argument("pack_path", help="Path to the content pack directory")
    parser.add_argument(
        "--download", action="store_true", help="Attempt to download remote assets"
    )

    args = parser.parse_args()
    success = resolve_assets(args.pack_path, args.download)
    sys.exit(0 if success else 1)
