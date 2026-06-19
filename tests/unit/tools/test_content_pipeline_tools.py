import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "tools" / "content"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from import_content_pack import import_pack  # noqa: E402
from run_content_pipeline import run_pipeline  # noqa: E402
from simulate_content_pack import simulate_pack  # noqa: E402
from validate_content_pack import validate_pack  # noqa: E402


def test_content_pipeline_dry_run_passes_valid_pack(tmp_path: Path) -> None:
    pack_dir = tmp_path / "generated"

    assert run_pipeline(42, "sylvan_supply", str(pack_dir))
    assert import_pack(str(pack_dir))

    report = json.loads((pack_dir / "import_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["mutated_database"] is False


def test_validate_pack_fails_invalid_pack(tmp_path: Path) -> None:
    pack_dir = tmp_path / "invalid"
    pack_dir.mkdir()
    (pack_dir / "pack.json").write_text(
        json.dumps(
            {
                "pack_id": "invalid",
                "version": "1.0.0",
                "npcs": [],
                "locations": [],
                "quests": [
                    {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "title": "Broken",
                        "giver_npc_id": "22222222-2222-2222-2222-222222222222",
                        "steps": [],
                    }
                ],
                "items": [],
            }
        ),
        encoding="utf-8",
    )

    assert not validate_pack(str(pack_dir))

    report = json.loads((pack_dir / "validation_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "FAIL"


def test_import_fails_when_validation_report_missing(tmp_path: Path) -> None:
    pack_dir = tmp_path / "generated"
    assert run_pipeline(42, "sylvan_supply", str(pack_dir))
    (pack_dir / "validation_report.json").unlink()

    assert not import_pack(str(pack_dir))

    report = json.loads((pack_dir / "import_report.json").read_text(encoding="utf-8"))
    assert "Missing required report: validation_report.json" in report["errors"]


def test_import_fails_when_simulation_failed(tmp_path: Path) -> None:
    pack_dir = tmp_path / "generated"
    assert run_pipeline(42, "sylvan_supply", str(pack_dir))

    pack = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    pack["quests"][0]["rewards"]["gold"] = -1
    (pack_dir / "pack.json").write_text(json.dumps(pack), encoding="utf-8")
    assert not simulate_pack(str(pack_dir))

    assert not import_pack(str(pack_dir))

    report = json.loads((pack_dir / "import_report.json").read_text(encoding="utf-8"))
    assert "simulation_report.json status is FAIL, expected PASS" in report["errors"]


def test_apply_without_approval_fails(tmp_path: Path) -> None:
    pack_dir = tmp_path / "generated"
    assert run_pipeline(42, "sylvan_supply", str(pack_dir))

    assert not import_pack(str(pack_dir), apply=True)

    report = json.loads((pack_dir / "import_report.json").read_text(encoding="utf-8"))
    assert "Apply mode requires --approve." in report["errors"]


def test_import_does_not_require_ai_suggestion(tmp_path: Path) -> None:
    from resolve_asset_manifest import resolve_assets

    pack_dir = tmp_path / "generated"
    source = REPO_ROOT / "content" / "packs" / "example_sylvan_supply"
    shutil.copytree(source, pack_dir)

    assert validate_pack(str(pack_dir))

    assert resolve_assets(str(pack_dir))
    assert simulate_pack(str(pack_dir))
    assert import_pack(str(pack_dir))
