import pytest

from app.engines.world import (
    QuestEngine,
    QuestRuleError,
    QuestStatus,
    RelationshipEngine,
)


def test_quest_engine_allows_only_canonical_transitions() -> None:
    accepted = QuestEngine.transition("NOT_STARTED", QuestStatus.ACTIVE)
    completed = QuestEngine.transition("ACTIVE", QuestStatus.COMPLETED)
    archived = QuestEngine.transition("COMPLETED", QuestStatus.ARCHIVED)

    assert accepted.current is QuestStatus.ACTIVE
    assert completed.current is QuestStatus.COMPLETED
    assert archived.current is QuestStatus.ARCHIVED
    with pytest.raises(QuestRuleError, match="cannot transition"):
        QuestEngine.transition("NOT_STARTED", QuestStatus.COMPLETED)
    with pytest.raises(QuestRuleError, match="cannot transition"):
        QuestEngine.transition("ARCHIVED", QuestStatus.ACTIVE)


def test_quest_progress_is_ordered_bounded_and_deterministic() -> None:
    partial = QuestEngine.advance_step(0, 2, 0, 2)
    complete_step = QuestEngine.advance_step(0, 2, partial[1], 2)
    final = QuestEngine.advance_step(1, 2, 0, 1)

    assert partial == (0, 1, False)
    assert complete_step == (1, 0, False)
    assert final == (2, 0, True)
    assert QuestEngine.advance_step(1, 2, 0, 1) == final
    with pytest.raises(QuestRuleError, match="positive"):
        QuestEngine.advance_step(0, 1, 0, 1, amount=0)


def test_relationship_engine_applies_only_known_clamped_dimensions() -> None:
    current = {field: 0 for field in RelationshipEngine.FIELDS}
    result = RelationshipEngine.apply(current, {"trust": 150, "hatred": -150, "respect": 4})

    assert result["trust"] == 100
    assert result["hatred"] == -100
    assert result["respect"] == 4
    with pytest.raises(QuestRuleError, match="Unknown"):
        RelationshipEngine.apply(current, {"affection": 1})
