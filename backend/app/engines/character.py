from dataclasses import dataclass
from uuid import UUID

STAT_NAMES = (
    "strength",
    "dexterity",
    "agility",
    "vitality",
    "intelligence",
    "wisdom",
    "charisma",
)
type PrerequisiteExpression = dict[str, object]


class CharacterRuleError(ValueError):
    """A deterministic character or progression rule was violated."""


@dataclass(frozen=True)
class CharacterStats:
    strength: int
    dexterity: int
    agility: int
    vitality: int
    intelligence: int
    wisdom: int
    charisma: int

    def as_dict(self) -> dict[str, int]:
        return {name: int(getattr(self, name)) for name in STAT_NAMES}


@dataclass(frozen=True)
class DerivedStats:
    max_hp: int
    max_mp: int
    max_stamina: int
    physical_attack: int
    physical_defense: int
    magic_attack: int
    magic_defense: int
    accuracy: int
    evasion: int
    critical_chance: float
    initiative: int


@dataclass(frozen=True)
class CharacterBuild:
    stats: CharacterStats
    derived: DerivedStats


@dataclass(frozen=True)
class ProgressionResult:
    level: int
    experience: int
    job_level: int
    job_experience: int
    skill_points: int
    stats: CharacterStats
    unlocked_skill_ids: tuple[UUID, ...]


class CharacterEngine:
    """Calculate character state from immutable definitions."""

    @staticmethod
    def create(
        base_stats: dict[str, int],
        racial_bonuses: dict[str, int],
        racial_penalties: dict[str, int],
        starting_job_modifiers: dict[str, int],
    ) -> CharacterBuild:
        values = {}
        for stat in STAT_NAMES:
            value = (
                int(base_stats.get(stat, 0))
                + int(racial_bonuses.get(stat, 0))
                - int(racial_penalties.get(stat, 0))
                + int(starting_job_modifiers.get(stat, 0))
            )
            if value < 1:
                raise CharacterRuleError(f"{stat} must remain positive")
            values[stat] = value
        stats = CharacterStats(**values)
        return CharacterBuild(stats=stats, derived=CharacterEngine.derive(stats))

    @staticmethod
    def derive(
        stats: CharacterStats,
        equipment_bonuses: dict[str, int] | None = None,
    ) -> DerivedStats:
        values = stats.as_dict()
        bonuses = equipment_bonuses or {}
        for key, value in bonuses.items():
            if key in values:
                values[key] += int(value)
        return DerivedStats(
            max_hp=50 + values["vitality"] * 10 + int(bonuses.get("max_hp", 0)),
            max_mp=10
            + values["intelligence"] * 4
            + values["wisdom"] * 3
            + int(bonuses.get("max_mp", 0)),
            max_stamina=50
            + values["vitality"] * 3
            + values["agility"] * 2
            + int(bonuses.get("max_stamina", 0)),
            physical_attack=values["strength"] * 2
            + values["dexterity"]
            + int(bonuses.get("physical_attack", 0)),
            physical_defense=values["vitality"] * 2
            + values["strength"] // 2
            + int(bonuses.get("physical_defense", 0)),
            magic_attack=values["intelligence"] * 2
            + values["wisdom"]
            + int(bonuses.get("magic_attack", 0)),
            magic_defense=values["wisdom"] * 2
            + values["vitality"] // 2
            + int(bonuses.get("magic_defense", 0)),
            accuracy=60 + values["dexterity"] * 2 + int(bonuses.get("accuracy", 0)),
            evasion=values["agility"] * 2 + int(bonuses.get("evasion", 0)),
            critical_chance=round(min(50.0, 2.0 + values["dexterity"] * 0.25), 2),
            initiative=values["agility"]
            + values["wisdom"] // 2
            + int(bonuses.get("initiative", 0)),
        )


class ProgressionEngine:
    """Apply deterministic character/job XP and evaluate job prerequisites."""

    CHARACTER_LEVEL_CAP = 100

    @staticmethod
    def experience_to_next(level: int) -> int:
        return 100 * level * level

    @staticmethod
    def job_experience_to_next(job_level: int) -> int:
        return 75 * job_level * job_level

    @classmethod
    def award_experience(
        cls,
        *,
        level: int,
        experience: int,
        job_level: int,
        job_experience: int,
        job_max_level: int,
        skill_points: int,
        stats: CharacterStats,
        job_stat_modifiers: dict[str, int],
        skill_unlocks: list[tuple[UUID, int]],
        already_unlocked: set[UUID],
        amount: int,
    ) -> ProgressionResult:
        if amount < 0:
            raise CharacterRuleError("Experience award cannot be negative")

        next_level = level
        remaining_experience = experience + amount
        next_stats = stats.as_dict()
        gained_skill_points = skill_points
        while (
            next_level < cls.CHARACTER_LEVEL_CAP
            and remaining_experience >= cls.experience_to_next(next_level)
        ):
            remaining_experience -= cls.experience_to_next(next_level)
            next_level += 1
            gained_skill_points += 1
            for stat in STAT_NAMES:
                next_stats[stat] += int(job_stat_modifiers.get(stat, 0))

        next_job_level = job_level
        remaining_job_experience = job_experience + amount
        while (
            next_job_level < job_max_level
            and remaining_job_experience >= cls.job_experience_to_next(next_job_level)
        ):
            remaining_job_experience -= cls.job_experience_to_next(next_job_level)
            next_job_level += 1

        unlocked = tuple(
            skill_id
            for skill_id, required_level in sorted(
                skill_unlocks, key=lambda value: (value[1], str(value[0]))
            )
            if required_level <= next_job_level and skill_id not in already_unlocked
        )
        return ProgressionResult(
            level=next_level,
            experience=remaining_experience,
            job_level=next_job_level,
            job_experience=remaining_job_experience,
            skill_points=gained_skill_points,
            stats=CharacterStats(**next_stats),
            unlocked_skill_ids=unlocked,
        )

    @classmethod
    def prerequisites_met(
        cls,
        expression: PrerequisiteExpression,
        *,
        character_level: int,
        karma: int,
        race_id: UUID,
        job_levels: dict[UUID, int],
    ) -> bool:
        if not expression:
            return True
        if "all" in expression:
            children = cls._children(expression["all"])
            return all(
                cls.prerequisites_met(
                    child,
                    character_level=character_level,
                    karma=karma,
                    race_id=race_id,
                    job_levels=job_levels,
                )
                for child in children
            )
        if "any" in expression:
            children = cls._children(expression["any"])
            return any(
                cls.prerequisites_met(
                    child,
                    character_level=character_level,
                    karma=karma,
                    race_id=race_id,
                    job_levels=job_levels,
                )
                for child in children
            )
        if "character_level_at_least" in expression:
            return character_level >= cls._integer(
                expression["character_level_at_least"]
            )
        if "karma_at_least" in expression:
            return karma >= cls._integer(expression["karma_at_least"])
        if "race_id" in expression:
            return race_id == UUID(str(expression["race_id"]))
        if "job_level" in expression:
            value = expression["job_level"]
            if not isinstance(value, dict):
                raise CharacterRuleError("job_level prerequisite must be an object")
            job_id = UUID(str(value["job_id"]))
            minimum = cls._integer(value["minimum"])
            return job_levels.get(job_id, 0) >= minimum
        raise CharacterRuleError("Unknown job prerequisite expression")

    @staticmethod
    def _children(value: object) -> list[PrerequisiteExpression]:
        if not isinstance(value, list) or not all(
            isinstance(child, dict) for child in value
        ):
            raise CharacterRuleError("Prerequisite branches must be object lists")
        return value

    @staticmethod
    def _integer(value: object) -> int:
        if isinstance(value, bool) or not isinstance(value, int | str):
            raise CharacterRuleError("Prerequisite value must be an integer")
        try:
            return int(value)
        except ValueError as error:
            raise CharacterRuleError("Prerequisite value must be an integer") from error
