from dataclasses import replace
from uuid import UUID

import pytest

from app.engines.combat import (
    CombatAction,
    CombatantState,
    CombatEngine,
    CombatRuleError,
    SeededRolls,
    StatusEffectState,
)

PLAYER_ID = UUID("10000000-0000-0000-0000-000000000001")
ENEMY_ID = UUID("20000000-0000-0000-0000-000000000001")


def _combatant(
    combatant_id: UUID,
    *,
    side: str,
    hp: int = 100,
    mp: int = 20,
    stamina: int = 20,
    attack: int = 30,
    defense: int = 10,
    magic: int = 25,
    magic_defense: int = 8,
    accuracy: int = 25,
    evasion: int = 5,
    critical: float = 0,
    initiative: int = 10,
    guarding: bool = False,
    statuses: tuple[StatusEffectState, ...] = (),
) -> CombatantState:
    return CombatantState(
        id=combatant_id,
        name="Hero" if side == "PLAYER" else "Enemy",
        side="PLAYER" if side == "PLAYER" else "ENEMY",
        level=1,
        hp=hp,
        max_hp=100,
        mp=mp,
        max_mp=20,
        stamina=stamina,
        max_stamina=20,
        physical_attack=attack,
        physical_defense=defense,
        magic_attack=magic,
        magic_defense=magic_defense,
        accuracy=accuracy,
        evasion=evasion,
        critical_chance=critical,
        initiative=initiative,
        guarding=guarding,
        statuses=statuses,
    )


def test_turn_order_is_deterministic_with_stable_tie_break() -> None:
    first = _combatant(PLAYER_ID, side="PLAYER", initiative=12)
    tied = _combatant(ENEMY_ID, side="ENEMY", initiative=12)

    assert CombatEngine.turn_order([tied, first]) == (PLAYER_ID, ENEMY_ID)
    assert CombatEngine.turn_order([first, tied]) == (PLAYER_ID, ENEMY_ID)
    assert CombatEngine.turn_order([replace(first, hp=0), tied]) == (ENEMY_ID,)


def test_identical_seeded_attacks_produce_identical_results() -> None:
    player = _combatant(PLAYER_ID, side="PLAYER", critical=25)
    enemy = _combatant(ENEMY_ID, side="ENEMY")
    action = CombatAction("ATTACK", target_id=ENEMY_ID, never_miss=True)

    first = CombatEngine.resolve_action(player, enemy, action, seed=741, sequence=3)
    second = CombatEngine.resolve_action(player, enemy, action, seed=741, sequence=3)

    assert first == second
    assert first.damage >= 1


def test_guard_halves_damage_and_expires_at_turn_start() -> None:
    player = _combatant(PLAYER_ID, side="PLAYER")
    enemy = _combatant(ENEMY_ID, side="ENEMY")
    guarded = CombatEngine.resolve_action(
        player,
        player,
        CombatAction("GUARD", target_id=PLAYER_ID),
        seed=1,
        sequence=0,
    ).actor
    normal = CombatEngine.resolve_action(
        enemy,
        player,
        CombatAction("ATTACK", target_id=PLAYER_ID, never_miss=True),
        seed=1,
        sequence=1,
    )
    reduced = CombatEngine.resolve_action(
        enemy,
        guarded,
        CombatAction("ATTACK", target_id=PLAYER_ID, never_miss=True),
        seed=1,
        sequence=1,
    )

    assert reduced.damage == max(1, normal.damage // 2)
    assert not CombatEngine.begin_turn(guarded).combatant.guarding


def test_fire_skill_spends_mp_and_applies_burn_to_survivor() -> None:
    player = _combatant(PLAYER_ID, side="PLAYER")
    enemy = _combatant(ENEMY_ID, side="ENEMY", hp=100)
    result = CombatEngine.resolve_action(
        player,
        enemy,
        CombatAction(
            "SKILL",
            target_id=ENEMY_ID,
            modifier_percent=125,
            resource_cost=5,
            effect="fire",
            never_miss=True,
        ),
        seed=9,
        sequence=0,
    )

    assert result.actor.mp == 15
    assert result.applied_statuses[0].code == "BURN"
    turn = CombatEngine.begin_turn(result.target)
    assert turn.combatant.hp < result.target.hp
    assert turn.combatant.statuses[0].duration == 1


def test_healing_and_barrier_skills_validate_and_spend_mp() -> None:
    wounded = _combatant(PLAYER_ID, side="PLAYER", hp=40, mp=10)
    healed = CombatEngine.resolve_action(
        wounded,
        wounded,
        CombatAction(
            "ITEM",
            target_id=PLAYER_ID,
            modifier_percent=25,
            resource_cost=6,
            effect="healing",
            skill_id=PLAYER_ID,
        ),
        seed=2,
        sequence=0,
    )
    guarded = CombatEngine.resolve_action(
        wounded,
        wounded,
        CombatAction("GUARD", resource_cost=4, skill_id=PLAYER_ID),
        seed=2,
        sequence=0,
    )

    assert healed.actor.hp == 65
    assert healed.actor.mp == 4
    assert guarded.actor.guarding
    assert guarded.actor.mp == 6
    with pytest.raises(CombatRuleError, match="Not enough MP"):
        CombatEngine.resolve_action(
            replace(wounded, mp=1),
            wounded,
            CombatAction("ITEM", modifier_percent=10, resource_cost=2, skill_id=PLAYER_ID),
            seed=2,
            sequence=0,
        )


def test_status_control_prevents_action_and_ticks_duration() -> None:
    stunned = _combatant(
        PLAYER_ID,
        side="PLAYER",
        statuses=(
            StatusEffectState("STUN", 2, 0),
            StatusEffectState("POISON", 1, 7),
        ),
    )

    result = CombatEngine.begin_turn(stunned)

    assert not result.can_act
    assert result.combatant.hp == 93
    assert result.combatant.statuses == (StatusEffectState("STUN", 1, 0),)


def test_enemy_policy_escape_and_rewards_are_seeded() -> None:
    player = _combatant(PLAYER_ID, side="PLAYER", initiative=20)
    enemy = _combatant(ENEMY_ID, side="ENEMY", hp=20, mp=10)

    assert (
        CombatEngine.enemy_action(enemy, player, round_number=2, skill_id=ENEMY_ID).action_type
        == "GUARD"
    )
    assert (
        CombatEngine.enemy_action(
            replace(enemy, hp=100), player, round_number=3, skill_id=ENEMY_ID
        ).action_type
        == "SKILL"
    )
    assert not CombatEngine.escape_succeeds(player, enemy, seed=5, sequence=0, escape_blocked=True)
    assert CombatEngine.rewards(
        experience=10, gold=5, loot_chance_percent=100, seed=7
    ) == CombatEngine.rewards(experience=10, gold=5, loot_chance_percent=100, seed=7)
    assert 1 <= SeededRolls.percent(7, 0, "loot") <= 100


def test_illegal_resources_and_reward_definitions_are_rejected() -> None:
    player = _combatant(PLAYER_ID, side="PLAYER", stamina=1)
    enemy = _combatant(ENEMY_ID, side="ENEMY")

    with pytest.raises(CombatRuleError, match="stamina"):
        CombatEngine.resolve_action(
            player,
            enemy,
            CombatAction(
                "SKILL",
                resource_cost=3,
                effect="physical",
                never_miss=True,
            ),
            seed=1,
            sequence=0,
        )
    with pytest.raises(CombatRuleError, match="negative"):
        CombatEngine.rewards(experience=-1, gold=0, loot_chance_percent=0, seed=1)
