import copy
import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_tool_module(module_name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(
        module_name, REPO_ROOT / relative_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validate_content_pack = _load_tool_module(
    "validate_content_pack", "tools/content/validate_content_pack.py"
)
resolve_asset_manifest = _load_tool_module(
    "resolve_asset_manifest", "tools/content/resolve_asset_manifest.py"
)


def _valid_pack() -> dict:
    location_id = "56000000-0000-0000-0000-000000000010"
    npc_id = "74000000-0000-0000-0000-000000000020"
    item_id = "54000000-0000-0000-0000-000000000030"
    quest_id = "75000000-0000-0000-0000-000000000040"

    return {
        "pack_id": "test_pack",
        "version": "1.0.0",
        "locations": [
            {
                "id": location_id,
                "name": "Test Grove",
                "region": "Valeria",
            }
        ],
        "npcs": [
            {
                "id": npc_id,
                "name": "Test Herbalist",
                "role": "HERBALIST",
                "home_location_id": location_id,
            }
        ],
        "items": [
            {
                "id": item_id,
                "name": "Test Petal",
                "type": "QUEST_ITEM",
                "base_value": 0,
            }
        ],
        "quests": [
            {
                "id": quest_id,
                "title": "Test Gathering",
                "giver_npc_id": npc_id,
                "steps": [
                    {
                        "objective_type": "FETCH",
                        "target_id": item_id,
                        "description": "Gather a test petal.",
                    }
                ],
            }
        ],
    }


def _write_pack(pack_dir: Path, pack: dict) -> None:
    pack_dir.mkdir()
    (pack_dir / "pack.json").write_text(json.dumps(pack), encoding="utf-8")


def _write_manifest(pack_dir: Path, manifest: dict) -> None:
    pack_dir.mkdir()
    (pack_dir / "assets.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_validate_pack_when_jsonschema_unavailable_fails_closed(
    tmp_path, monkeypatch, capsys
):
    pack_dir = tmp_path / "pack"
    _write_pack(pack_dir, _valid_pack())
    monkeypatch.setattr(validate_content_pack, "Draft7Validator", None)
    monkeypatch.setattr(validate_content_pack, "FormatChecker", None)
    monkeypatch.setattr(
        validate_content_pack,
        "JSONSCHEMA_IMPORT_ERROR",
        ImportError("jsonschema missing"),
    )

    assert validate_content_pack.validate_pack(str(pack_dir)) is False
    assert "jsonschema is required" in capsys.readouterr().out


def test_validate_pack_rejects_invalid_uuid_format(tmp_path, capsys):
    pack = _valid_pack()
    pack["npcs"][0]["id"] = "not-a-uuid"
    pack_dir = tmp_path / "pack"
    _write_pack(pack_dir, pack)

    assert validate_content_pack.validate_pack(str(pack_dir)) is False
    output = capsys.readouterr().out
    assert "Schema validation error" in output
    assert "uuid" in output


def test_validate_pack_rejects_duplicate_content_ids(tmp_path, capsys):
    pack = _valid_pack()
    duplicate_id = pack["locations"][0]["id"]
    pack["items"][0]["id"] = duplicate_id
    pack["quests"][0]["steps"][0]["target_id"] = duplicate_id
    pack_dir = tmp_path / "pack"
    _write_pack(pack_dir, pack)

    assert validate_content_pack.validate_pack(str(pack_dir)) is False
    assert "Duplicate content id" in capsys.readouterr().out


def test_resolve_assets_requires_existing_file_for_local_assets(tmp_path):
    pack_dir = tmp_path / "pack"
    _write_manifest(
        pack_dir,
        {
            "pack_id": "asset_pack",
            "assets": [
                {
                    "asset_id": "missing_local",
                    "type": "sprite",
                    "license": "CC0",
                    "status": "local",
                }
            ],
        },
    )

    assert resolve_asset_manifest.resolve_assets(str(pack_dir)) is False
    report = json.loads(
        (pack_dir / "asset_resolution_report.json").read_text(encoding="utf-8")
    )
    assert report["resolution_results"][0]["status"] == "missing"


def test_resolve_assets_parses_remote_host_before_allowlisting(tmp_path):
    pack_dir = tmp_path / "pack"
    manifest = {
        "pack_id": "asset_pack",
        "assets": [
            {
                "asset_id": "host_spoof",
                "type": "sprite",
                "license": "CC0",
                "status": "missing",
                "remote_url": "https://kenney.nl.evil.example/assets/sprite.png",
            }
        ],
    }
    _write_manifest(pack_dir, copy.deepcopy(manifest))

    assert resolve_asset_manifest.resolve_assets(str(pack_dir), download=True) is False
    report = json.loads(
        (pack_dir / "asset_resolution_report.json").read_text(encoding="utf-8")
    )
    assert report["resolution_results"][0]["status"] == "blocked"
    assert "Domain not in allowlist" in report["resolution_results"][0]["notes"][0]
