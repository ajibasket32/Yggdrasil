from uuid import UUID, uuid4

import pytest

from app.engines.character import (
    CharacterEngine,
    CharacterStats,
    ProgressionEngine,
)
from app.engines.equipment import (
    EquipmentCandidate,
    EquipmentEngine,
    EquipmentRuleError,
)
from app.engines.inventory import (
    InventoryEngine,
    InventoryEntry,
    InventoryRuleError,
    ItemRule,
)
from app.engines.navigation import (
    NavigationEngine,
    NavigationRuleError,
    TravelRoute,
)


def test_character_creation_is_deterministic() -> None:
    base = {
        "strength": 10,
        "dexterity": 10,
        "agility": 10,
        "vitality": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10,
    }
    arguments = (base, {"strength": 2}, {"charisma": 1}, {"vitality": 3})

    first = CharacterEngine.create(*arguments)
    second = CharacterEngine.create(*arguments)

    assert first == second
    assert first.stats.strength == 12
    assert first.stats.charisma == 9
    assert first.derived.max_hp == 180


def test_progression_applies_identical_levels_stats_and_unlocks() -> None:
    skill_id = uuid4()
    arguments = {
        "level": 1,
        "experience": 0,
        "job_level": 1,
        "job_experience": 0,
        "job_max_level": 15,
        "skill_points": 0,
        "stats": CharacterStats(10, 10, 10, 10, 10, 10, 10),
        "job_stat_modifiers": {"strength": 3, "vitality": 2},
        "skill_unlocks": [(skill_id, 2)],
        "already_unlocked": set(),
        "amount": 200,
    }

    first = ProgressionEngine.award_experience(**arguments)
    second = ProgressionEngine.award_experience(**arguments)

    assert first == second
    assert first.level == 2
    assert first.job_level == 2
    assert first.stats.strength == 13
    assert first.unlocked_skill_ids == (skill_id,)


def test_branching_job_prerequisites_support_all_and_any() -> None:
    warrior = uuid4()
    cleric = uuid4()
    expression = {
        "all": [
            {"job_level": {"job_id": str(warrior), "minimum": 10}},
            {
                "any": [
                    {"job_level": {"job_id": str(cleric), "minimum": 5}},
                    {"karma_at_least": 100},
                ]
            },
        ]
    }

    assert ProgressionEngine.prerequisites_met(
        expression,
        character_level=20,
        karma=120,
        race_id=uuid4(),
        job_levels={warrior: 10},
    )
    assert not ProgressionEngine.prerequisites_met(
        expression,
        character_level=20,
        karma=0,
        race_id=uuid4(),
        job_levels={warrior: 10, cleric: 4},
    )


def test_inventory_stack_rules_and_quest_item_protection() -> None:
    item_id = uuid4()
    entry = InventoryEntry(uuid4(), item_id, 18, 0, None)
    stack_rule = ItemRule(item_id, 0.5, True, 20, False, True)

    updates, creates = InventoryEngine.plan_add(
        [entry],
        stack_rule,
        5,
        slot_count=4,
        current_weight=9,
        max_weight=100,
    )

    assert updates == [(entry.entry_id, 20)]
    assert creates[0].quantity == 3
    assert creates[0].slot_index == 1

    quest_rule = ItemRule(item_id, 0.1, False, 1, True, False)
    with pytest.raises(InventoryRuleError, match="cannot be dropped"):
        InventoryEngine.validate_drop(entry, quest_rule, 1)


def test_unique_items_get_distinct_instances() -> None:
    item_id = uuid4()
    rule = ItemRule(item_id, 1, False, 1, False, True)

    _, creates = InventoryEngine.plan_add(
        [],
        rule,
        2,
        slot_count=3,
        current_weight=0,
        max_weight=10,
    )

    assert len(creates) == 2
    assert creates[0].unique_instance_id != creates[1].unique_instance_id


def test_equipment_and_navigation_reject_invalid_actions() -> None:
    candidate = EquipmentCandidate(uuid4(), 1, 1, ("main_hand",))
    EquipmentEngine.validate_equip(candidate, slot_code="main_hand", character_level=1)
    with pytest.raises(EquipmentRuleError, match="compatible"):
        EquipmentEngine.validate_equip(candidate, slot_code="helmet", character_level=1)

    origin = uuid4()
    destination = uuid4()
    valid_route = TravelRoute(origin, destination, {})
    assert (
        NavigationEngine.validate_travel(
            origin, destination, [valid_route], character_level=1
        )
        == valid_route
    )
    with pytest.raises(NavigationRuleError, match="No direct route"):
        NavigationEngine.validate_travel(
            origin, UUID(int=0), [valid_route], character_level=1
        )
