from dataclasses import dataclass
from enum import StrEnum


class QuestStatus(StrEnum):
    """Only states permitted by the canonical quest contract."""

    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class QuestRuleError(ValueError):
    """A deterministic quest or relationship rule was violated."""


@dataclass(frozen=True)
class QuestTransition:
    """Result of one valid quest state transition."""

    previous: QuestStatus
    current: QuestStatus


class QuestEngine:
    """Pure state-machine and progress rules for canonical quests."""

    _TRANSITIONS = {
        QuestStatus.NOT_STARTED: frozenset({QuestStatus.ACTIVE}),
        QuestStatus.ACTIVE: frozenset({QuestStatus.COMPLETED, QuestStatus.FAILED}),
        QuestStatus.COMPLETED: frozenset({QuestStatus.ARCHIVED}),
        QuestStatus.FAILED: frozenset({QuestStatus.ARCHIVED}),
        QuestStatus.ARCHIVED: frozenset(),
    }

    @classmethod
    def transition(cls, current: str, requested: QuestStatus) -> QuestTransition:
        """Validate and return one transition without side effects."""
        try:
            previous = QuestStatus(current)
        except ValueError as error:
            raise QuestRuleError("Unknown quest state") from error
        if requested not in cls._TRANSITIONS[previous]:
            raise QuestRuleError(
                f"Quest cannot transition from {previous.value} to {requested.value}"
            )
        return QuestTransition(previous=previous, current=requested)

    @staticmethod
    def advance_step(
        current_step: int,
        step_count: int,
        current_progress: int,
        required_count: int,
        amount: int = 1,
    ) -> tuple[int, int, bool]:
        """Advance one ordered quest objective deterministically."""
        if amount <= 0 or required_count <= 0:
            raise QuestRuleError("Quest progress values must be positive")
        if current_step < 0 or current_step >= step_count:
            raise QuestRuleError("Quest has no active objective")
        progress = min(required_count, current_progress + amount)
        if progress < required_count:
            return current_step, progress, False
        next_step = current_step + 1
        return next_step, 0, next_step >= step_count

    @staticmethod
    def validate_acceptance(
        character_level: int,
        minimum_level: int,
        prerequisites_complete: bool,
    ) -> None:
        """Validate level and prerequisite gates."""
        if character_level < minimum_level:
            raise QuestRuleError("Character level is below the quest requirement")
        if not prerequisites_complete:
            raise QuestRuleError("Quest prerequisites are not complete")

    @staticmethod
    def rewards(definition: dict[str, object]) -> tuple[int, int, int]:
        """Read engine-owned XP, gold, and faction reputation rewards."""
        experience = QuestEngine._reward_value(definition, "experience")
        gold = QuestEngine._reward_value(definition, "gold")
        reputation = QuestEngine._reward_value(definition, "reputation")
        if experience < 0 or gold < 0:
            raise QuestRuleError("Quest rewards cannot be negative")
        return experience, gold, reputation

    @staticmethod
    def _reward_value(definition: dict[str, object], key: str) -> int:
        value = definition.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, int):
            raise QuestRuleError("Quest rewards must be integer values")
        return value


class RelationshipEngine:
    """Clamp deterministic relationship deltas to canonical bounds."""

    MINIMUM = -100
    MAXIMUM = 100
    FIELDS = ("trust", "friendship", "respect", "fear", "hatred", "loyalty")

    @classmethod
    def apply(cls, current: dict[str, int], deltas: dict[str, int]) -> dict[str, int]:
        """Return relationship values after approved action deltas."""
        unknown = set(deltas) - set(cls.FIELDS)
        if unknown:
            raise QuestRuleError("Unknown relationship dimension")
        return {
            field: max(
                cls.MINIMUM,
                min(cls.MAXIMUM, current.get(field, 0) + deltas.get(field, 0)),
            )
            for field in cls.FIELDS
        }
