import hashlib
from dataclasses import dataclass, replace
from typing import Literal
from uuid import UUID

ActionType = Literal["ATTACK", "SKILL", "ITEM", "GUARD", "WAIT"]
Element = Literal[
    "NONE",
    "FIRE",
    "WATER",
    "ICE",
    "EARTH",
    "WIND",
    "LIGHTNING",
    "HOLY",
    "DARK",
    "ARCANE",
    "NATURE",
]


class CombatRuleError(ValueError):
    """A deterministic combat rule was violated."""


@dataclass(frozen=True)
class StatusEffectState:
    code: str
    duration: int
    potency: int


@dataclass(frozen=True)
class CombatantState:
    id: UUID
    name: str
    side: Literal["PLAYER", "ENEMY"]
    level: int
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    stamina: int
    max_stamina: int
    physical_attack: int
    physical_defense: int
    magic_attack: int
    magic_defense: int
    accuracy: int
    evasion: int
    critical_chance: float
    initiative: int
    guarding: bool = False
    statuses: tuple[StatusEffectState, ...] = ()

    @property
    def defeated(self) -> bool:
        return self.hp <= 0


@dataclass(frozen=True)
class CombatAction:
    action_type: ActionType
    target_id: UUID | None = None
    skill_id: UUID | None = None
    item_id: UUID | None = None
    modifier_percent: int = 100
    resource_cost: int = 0
    effect: str = "physical"
    never_miss: bool = False


@dataclass(frozen=True)
class ActionResolution:
    actor: CombatantState
    target: CombatantState
    hit: bool
    critical: bool
    damage: int
    healing: int
    applied_statuses: tuple[StatusEffectState, ...]
    log_lines: tuple[str, ...]


@dataclass(frozen=True)
class TurnStart:
    combatant: CombatantState
    can_act: bool
    log_lines: tuple[str, ...]


@dataclass(frozen=True)
class RewardResult:
    experience: int
    gold: int
    loot_awarded: bool


class SeededRolls:
    """Stateless deterministic rolls derived from one encounter seed."""

    @staticmethod
    def percent(seed: int, sequence: int, purpose: str) -> int:
        digest = hashlib.sha256(f"{seed}:{sequence}:{purpose}".encode("ascii")).digest()
        return int.from_bytes(digest[:8], "big") % 100 + 1


class CombatEngine:
    """Pure, network-free authority for turn combat."""

    ELEMENT_ADVANTAGE: dict[tuple[str, str], int] = {
        ("FIRE", "ICE"): 150,
        ("ICE", "WATER"): 150,
        ("LIGHTNING", "WATER"): 150,
        ("HOLY", "UNDEAD"): 200,
        ("DARK", "HOLY"): 150,
        ("NATURE", "EARTH"): 150,
        ("ARCANE", "BARRIER"): 150,
    }

    @staticmethod
    def turn_order(combatants: list[CombatantState]) -> tuple[UUID, ...]:
        active = [combatant for combatant in combatants if not combatant.defeated]
        return tuple(
            combatant.id
            for combatant in sorted(
                active,
                key=lambda value: (-value.initiative, str(value.id)),
            )
        )

    @staticmethod
    def begin_turn(combatant: CombatantState) -> TurnStart:
        hp = combatant.hp
        can_act = True
        next_statuses: list[StatusEffectState] = []
        logs: list[str] = []
        for status in combatant.statuses:
            if status.code in {"BURN", "POISON", "BLEED"}:
                damage = min(hp, max(1, status.potency))
                hp -= damage
                logs.append(f"{combatant.name} suffers {damage} {status.code.lower()} damage.")
            if status.code in {"STUN", "SLEEP", "FREEZE"}:
                can_act = False
                logs.append(f"{combatant.name} cannot act due to {status.code.lower()}.")
            if status.duration > 1:
                next_statuses.append(replace(status, duration=status.duration - 1))
        return TurnStart(
            combatant=replace(
                combatant,
                hp=hp,
                guarding=False,
                statuses=tuple(next_statuses),
            ),
            can_act=can_act and hp > 0,
            log_lines=tuple(logs),
        )

    @classmethod
    def resolve_action(
        cls,
        actor: CombatantState,
        target: CombatantState,
        action: CombatAction,
        *,
        seed: int,
        sequence: int,
    ) -> ActionResolution:
        if actor.defeated:
            raise CombatRuleError("Defeated combatants cannot act")
        if action.action_type in {"ATTACK", "SKILL"} and target.defeated:
            raise CombatRuleError("Defeated targets cannot be selected")
        if action.action_type == "GUARD":
            if action.resource_cost > actor.mp:
                raise CombatRuleError("Not enough MP")
            guarded = replace(
                actor,
                guarding=True,
                mp=actor.mp - action.resource_cost,
            )
            return ActionResolution(
                guarded,
                target,
                True,
                False,
                0,
                0,
                (),
                (f"{actor.name} takes a guarded stance.",),
            )
        if action.action_type == "WAIT":
            return ActionResolution(
                actor,
                target,
                True,
                False,
                0,
                0,
                (),
                (f"{actor.name} waits.",),
            )
        if action.action_type == "ITEM":
            if action.resource_cost > actor.mp:
                raise CombatRuleError("Not enough MP")
            healing = max(0, action.modifier_percent)
            restored = min(healing, actor.max_hp - actor.hp)
            updated = replace(
                actor,
                hp=actor.hp + restored,
                mp=(actor.mp - action.resource_cost if action.skill_id is not None else actor.mp),
            )
            return ActionResolution(
                updated,
                target,
                True,
                False,
                0,
                restored,
                (),
                (f"{actor.name} restores {restored} HP.",),
            )

        magical = action.effect in {
            "fire",
            "water",
            "ice",
            "earth",
            "wind",
            "lightning",
            "holy",
            "dark",
            "arcane",
            "nature",
        }
        if magical and actor.mp < action.resource_cost:
            raise CombatRuleError("Not enough MP")
        if not magical and action.resource_cost and actor.stamina < action.resource_cost:
            raise CombatRuleError("Not enough stamina")

        hit_chance = max(5, min(95, 75 + actor.accuracy - target.evasion))
        hit = action.never_miss or (SeededRolls.percent(seed, sequence, "hit") <= hit_chance)
        next_actor = replace(
            actor,
            mp=actor.mp - action.resource_cost if magical else actor.mp,
            stamina=(actor.stamina - action.resource_cost if not magical else actor.stamina),
        )
        if not hit:
            return ActionResolution(
                next_actor,
                target,
                False,
                False,
                0,
                0,
                (),
                (f"{actor.name}'s action misses {target.name}.",),
            )

        attack = actor.magic_attack if magical else actor.physical_attack
        defense = target.magic_defense if magical else target.physical_defense
        base = max(1, attack * action.modifier_percent // 100 - defense)
        critical = SeededRolls.percent(seed, sequence, "critical") <= actor.critical_chance
        if critical:
            base = base * 3 // 2
        element = action.effect.upper()
        target_kind = next(
            (
                status.code.removeprefix("AFFINITY_")
                for status in target.statuses
                if status.code.startswith("AFFINITY_")
            ),
            "NONE",
        )
        base = base * cls.ELEMENT_ADVANTAGE.get((element, target_kind), 100) // 100
        if target.guarding:
            base = max(1, base // 2)
        damage = min(target.hp, base)
        statuses: tuple[StatusEffectState, ...] = ()
        if action.effect == "fire" and target.hp - damage > 0:
            statuses = (
                StatusEffectState(
                    code="BURN",
                    duration=2,
                    potency=max(1, actor.magic_attack // 10),
                ),
            )
        updated_target = replace(
            target,
            hp=target.hp - damage,
            statuses=target.statuses + statuses,
        )
        label = "critical " if critical else ""
        logs = [f"{actor.name} deals {damage} {label}damage to {target.name}."]
        if updated_target.defeated:
            logs.append(f"{target.name} is defeated.")
        return ActionResolution(
            next_actor,
            updated_target,
            True,
            critical,
            damage,
            0,
            statuses,
            tuple(logs),
        )

    @staticmethod
    def enemy_action(
        enemy: CombatantState,
        player: CombatantState,
        *,
        round_number: int,
        skill_id: UUID | None,
    ) -> CombatAction:
        if enemy.hp * 4 <= enemy.max_hp and round_number % 2 == 0:
            return CombatAction("GUARD", target_id=enemy.id)
        if skill_id is not None and enemy.mp >= 4 and round_number % 3 == 0:
            return CombatAction(
                "SKILL",
                target_id=player.id,
                skill_id=skill_id,
                modifier_percent=120,
                resource_cost=4,
                effect="fire",
            )
        return CombatAction("ATTACK", target_id=player.id)

    @staticmethod
    def escape_succeeds(
        player: CombatantState,
        enemy: CombatantState,
        *,
        seed: int,
        sequence: int,
        escape_blocked: bool,
    ) -> bool:
        if escape_blocked:
            return False
        chance = max(10, min(90, 50 + (player.initiative - enemy.initiative) * 3))
        return SeededRolls.percent(seed, sequence, "escape") <= chance

    @staticmethod
    def rewards(
        *,
        experience: int,
        gold: int,
        loot_chance_percent: int,
        seed: int,
    ) -> RewardResult:
        if min(experience, gold, loot_chance_percent) < 0:
            raise CombatRuleError("Reward definitions cannot be negative")
        return RewardResult(
            experience=experience,
            gold=gold,
            loot_awarded=SeededRolls.percent(seed, 0, "loot") <= loot_chance_percent,
        )
