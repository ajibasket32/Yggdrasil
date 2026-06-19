import json
import shutil
import sys
from collections.abc import Callable
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "tools" / "content"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))


def _load_tool_module(module_name: str) -> ModuleType:
    spec = util.spec_from_file_location(module_name, TOOLS_DIR / f"{module_name}.py")
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load content tool module: {module_name}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


import_pack = cast(
    Callable[[str, bool, bool], bool],
    _load_tool_module("import_content_pack").import_pack,
)
run_pipeline = cast(
    Callable[[int, str, str, bool], bool],
    _load_tool_module("run_content_pipeline").run_pipeline,
)
simulate_pack = cast(
    Callable[[str], bool],
    _load_tool_module("simulate_content_pack").simulate_pack,
)
validate_pack = cast(
    Callable[[str], bool],
    _load_tool_module("validate_content_pack").validate_pack,
)
resolve_assets = cast(
    Callable[[str, bool], bool],
    _load_tool_module("resolve_asset_manifest").resolve_assets,
)


def test_content_pipeline_dry_run_passes_valid_pack(tmp_path: Path) -> None:
    pack_dir = tmp_path / "generated"

    assert run_pipeline(42, "sylvan_supply", str(pack_dir), False)
    assert import_pack(str(pack_dir), False, False)

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

    report = json.loads(
        (pack_dir / "validation_report.json").read_text(encoding="utf-8")
    )
    assert report["status"] == "FAIL"


def test_import_fails_when_validation_report_missing(tmp_path: Path) -> None:
    pack_dir = tmp_path / "generated"
    assert run_pipeline(42, "sylvan_supply", str(pack_dir), False)
    (pack_dir / "validation_report.json").unlink()

    assert not import_pack(str(pack_dir), False, False)

    report = json.loads((pack_dir / "import_report.json").read_text(encoding="utf-8"))
    assert "Missing required report: validation_report.json" in report["errors"]


def test_import_fails_when_simulation_failed(tmp_path: Path) -> None:
    pack_dir = tmp_path / "generated"
    assert run_pipeline(42, "sylvan_supply", str(pack_dir), False)

    pack = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    pack["quests"][0]["rewards"]["gold"] = -1
    (pack_dir / "pack.json").write_text(json.dumps(pack), encoding="utf-8")
    assert not simulate_pack(str(pack_dir))

    assert not import_pack(str(pack_dir), False, False)

    report = json.loads((pack_dir / "import_report.json").read_text(encoding="utf-8"))
    assert "simulation_report.json status is FAIL, expected PASS" in report["errors"]


def test_apply_without_approval_fails(tmp_path: Path) -> None:
    pack_dir = tmp_path / "generated"
    assert run_pipeline(42, "sylvan_supply", str(pack_dir), False)

    assert not import_pack(str(pack_dir), True, False)

    report = json.loads((pack_dir / "import_report.json").read_text(encoding="utf-8"))
    assert "Apply mode requires --approve." in report["errors"]


def test_import_does_not_require_ai_suggestion(tmp_path: Path) -> None:
    pack_dir = tmp_path / "generated"
    source = REPO_ROOT / "content" / "packs" / "example_sylvan_supply"
    shutil.copytree(source, pack_dir)

    assert validate_pack(str(pack_dir))

    assert resolve_assets(str(pack_dir), False)
    assert simulate_pack(str(pack_dir))
    assert import_pack(str(pack_dir), False, False)
