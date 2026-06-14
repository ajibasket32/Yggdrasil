from copy import deepcopy

import pytest

from app.schemas.save import SaveSnapshotV1
from app.services.save import SaveCompatibilityError, SaveMigrator, SaveService


def test_snapshot_contract_contains_every_required_save_component() -> None:
    snapshot = SaveSnapshotV1()

    assert set(snapshot.model_dump()) == {
        "schema_version",
        "world_tick",
        "character",
        "inventory",
        "equipment",
        "world_state",
        "quest_state",
        "npc_state",
        "faction_state",
        "relationships",
        "journal",
        "memories",
        "dungeon_state",
    }


def test_checksum_is_deterministic_and_detects_changes() -> None:
    original = SaveSnapshotV1(
        world_tick=42,
        character={"name": "Momonga"},
    ).model_dump(mode="json")
    reordered = {"character": original["character"], **original}
    changed = deepcopy(original)
    changed["world_tick"] = 43

    assert SaveService.checksum(original) == SaveService.checksum(reordered)
    assert SaveService.checksum(original) != SaveService.checksum(changed)


def test_legacy_snapshot_migrates_with_empty_future_components() -> None:
    migrated = SaveMigrator.migrate(
        {
            "schema_version": 0,
            "world_tick": 7,
            "character_state": {"name": "Legacy"},
            "world": {"season": "winter"},
        },
        0,
    )

    assert migrated.schema_version == 1
    assert migrated.character == {"name": "Legacy"}
    assert migrated.world_state == {"season": "winter"}
    assert migrated.inventory == {}


def test_unknown_snapshot_version_fails_with_actionable_error() -> None:
    with pytest.raises(SaveCompatibilityError, match="supported versions are 0 and 1"):
        SaveMigrator.migrate({"schema_version": 99}, 99)
