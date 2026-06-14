from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.core.database import session_factory
from app.engines.combat import SeededRolls
from app.models.combat import CombatEncounter, CombatParticipant
from app.models.gameplay import Character
from app.repositories.combat import CombatUnitOfWork
from app.repositories.gameplay import GameStateRepository, GameUnitOfWork
from app.repositories.save import SaveUnitOfWork
from app.schemas.combat import CombatActionRequest, StartCombatRequest
from app.schemas.gameplay import CreateCharacterRequest
from app.services.combat import CombatConflictError, CombatService
from app.services.gameplay import (
    CharacterService,
    DefinitionNotFoundError,
    GameplayIdempotencyConflict,
    GameplayRuleViolation,
)
from app.services.save import SaveActiveCombatError, SaveService


async def _ready_character(player_id: UUID, job_name: str = "Alchemist"):
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        definitions = await service.creation_definitions()
        job = next(
            value for value in definitions.starting_jobs if value.name == job_name
        )
        character = await service.create_character(
            player_id,
            CreateCharacterRequest(
                name=f"{job_name} Tester",
                race_id=definitions.races[0].id,
                gender="Unspecified",
                alignment="NEUTRAL",
                starting_job_id=job.id,
            ),
            f"create-{player_id}",
        )
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        locations = await service.locations(player_id, character.id)
        greenwood = next(
            value for value in locations if value.name == "Greenwood Verge"
        )
        await service.travel(
            player_id,
            character.id,
            greenwood.id,
            f"travel-{player_id}",
        )
    return character


async def _start(player_id: UUID, character_id: UUID, seed: int):
    async with session_factory() as session:
        service = CombatService(CombatUnitOfWork(session))
        definition = (await service.available_encounters(player_id, character_id))[0]
        state = await service.start(
            player_id,
            StartCombatRequest(
                character_id=character_id,
                encounter_definition_id=definition.id,
                seed=seed,
            ),
            f"start-{character_id}-{seed}",
        )
    return definition, state


async def _act(
    player_id: UUID,
    request: CombatActionRequest,
    key: str,
):
    async with session_factory() as session:
        return await CombatService(CombatUnitOfWork(session)).act(
            player_id, request, key
        )


@pytest.mark.asyncio
async def test_guard_wait_healing_skill_and_consumable_actions_persist(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character = await _ready_character(player_id)
    _, state = await _start(player_id, character.id, 101)
    player = next(value for value in state.participants if value.side == "PLAYER")

    state = await _act(
        player_id,
        CombatActionRequest(combat_id=state.combat_id, action_type="WAIT"),
        "wait-action",
    )
    wounded = next(value for value in state.participants if value.side == "PLAYER")
    assert wounded.current_hp < player.current_hp

    skill = character.skills[0]
    state = await _act(
        player_id,
        CombatActionRequest(
            combat_id=state.combat_id,
            action_type="SKILL",
            skill_id=skill.id,
        ),
        "healing-skill",
    )
    healed = next(value for value in state.participants if value.side == "PLAYER")
    assert healed.current_mp == wounded.current_mp - skill.mana_cost

    async with session_factory() as session:
        inventory = await CharacterService(GameUnitOfWork(session)).inventory(
            player_id, character.id
        )
    potion = next(value for value in inventory.items if value.name == "Field Potion")
    state = await _act(
        player_id,
        CombatActionRequest(
            combat_id=state.combat_id,
            action_type="ITEM",
            inventory_item_id=potion.inventory_item_id,
        ),
        "potion-action",
    )
    state = await _act(
        player_id,
        CombatActionRequest(combat_id=state.combat_id, action_type="GUARD"),
        "guard-action",
    )

    assert state.status == "ACTIVE"
    assert any(entry.action_type == "ITEM" for entry in state.recent_log)
    assert any(entry.action_type == "GUARD" for entry in state.recent_log)
    async with session_factory() as session:
        remaining = await CharacterService(GameUnitOfWork(session)).inventory(
            player_id, character.id
        )
    assert (
        next(
            value for value in remaining.items if value.name == "Field Potion"
        ).quantity
        == potion.quantity - 1
    )


@pytest.mark.asyncio
async def test_offensive_and_barrier_skills_use_engine_owned_resources(
    clean_gameplay_database: None,
) -> None:
    mage_player = uuid4()
    mage = await _ready_character(mage_player, "Mage")
    _, mage_state = await _start(mage_player, mage.id, 202)
    enemy_before = next(
        value for value in mage_state.participants if value.side == "ENEMY"
    )
    mage_state = await _act(
        mage_player,
        CombatActionRequest(
            combat_id=mage_state.combat_id,
            action_type="SKILL",
            skill_id=mage.skills[0].id,
        ),
        "mage-skill",
    )
    enemy_after = next(
        value for value in mage_state.participants if value.side == "ENEMY"
    )
    assert enemy_after.current_hp < enemy_before.current_hp

    druid_player = uuid4()
    druid = await _ready_character(druid_player, "Druid")
    _, druid_state = await _start(druid_player, druid.id, 303)
    druid_before = next(
        value for value in druid_state.participants if value.side == "PLAYER"
    )
    druid_state = await _act(
        druid_player,
        CombatActionRequest(
            combat_id=druid_state.combat_id,
            action_type="SKILL",
            skill_id=druid.skills[0].id,
        ),
        "barrier-skill",
    )
    druid_after = next(
        value for value in druid_state.participants if value.side == "PLAYER"
    )
    assert druid_after.current_mp == druid_before.current_mp - druid.skills[0].mana_cost
    assert druid_after.guarding


@pytest.mark.asyncio
async def test_escape_success_failure_and_retry_are_deterministic(
    clean_gameplay_database: None,
) -> None:
    success_seed = next(
        seed for seed in range(1000) if SeededRolls.percent(seed, 0, "escape") <= 10
    )
    failure_seed = next(
        seed for seed in range(1000) if SeededRolls.percent(seed, 0, "escape") > 90
    )

    success_player = uuid4()
    success_character = await _ready_character(success_player)
    _, success_state = await _start(success_player, success_character.id, success_seed)
    async with session_factory() as session:
        service = CombatService(CombatUnitOfWork(session))
        escaped = await service.flee(
            success_player, success_state.combat_id, "escape-success"
        )
    async with session_factory() as session:
        replayed = await CombatService(CombatUnitOfWork(session)).flee(
            success_player, success_state.combat_id, "escape-success"
        )
    assert escaped.status == "FLED"
    assert replayed == escaped

    failure_player = uuid4()
    failure_character = await _ready_character(failure_player)
    _, failure_state = await _start(failure_player, failure_character.id, failure_seed)
    before = next(
        value for value in failure_state.participants if value.side == "PLAYER"
    )
    async with session_factory() as session:
        failed = await CombatService(CombatUnitOfWork(session)).flee(
            failure_player, failure_state.combat_id, "escape-failure"
        )
    after = next(value for value in failed.participants if value.side == "PLAYER")
    assert failed.status == "ACTIVE"
    assert after.current_hp < before.current_hp


@pytest.mark.asyncio
async def test_defeat_sets_recovery_hp_and_blocks_future_actions(
    clean_gameplay_database: None,
) -> None:
    seed = next(
        value for value in range(1000) if SeededRolls.percent(value, 1, "hit") <= 90
    )
    player_id = uuid4()
    character = await _ready_character(player_id)
    _, state = await _start(player_id, character.id, seed)
    async with session_factory() as session, session.begin():
        participant = (
            await session.execute(
                select(CombatParticipant).where(
                    CombatParticipant.encounter_id == state.combat_id,
                    CombatParticipant.side == "PLAYER",
                )
            )
        ).scalar_one()
        participant.current_hp = 1

    defeated = await _act(
        player_id,
        CombatActionRequest(combat_id=state.combat_id, action_type="WAIT"),
        "wait-for-defeat",
    )
    assert defeated.status == "DEFEAT"
    async with session_factory() as session:
        canonical = await CharacterService(GameUnitOfWork(session)).get_character(
            player_id, character.id
        )
    assert canonical.current_hp == 1
    with pytest.raises(CombatConflictError, match="already complete"):
        await _act(
            player_id,
            CombatActionRequest(combat_id=state.combat_id, action_type="ATTACK"),
            "post-defeat-action",
        )


@pytest.mark.asyncio
async def test_start_validation_and_idempotency_guards_canonical_state(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character = await _ready_character(player_id)
    async with session_factory() as session:
        service = CombatService(CombatUnitOfWork(session))
        definition = (await service.available_encounters(player_id, character.id))[0]
    request = StartCombatRequest(
        character_id=character.id,
        encounter_definition_id=definition.id,
        seed=404,
    )
    async with session_factory() as session:
        first = await CombatService(CombatUnitOfWork(session)).start(
            player_id, request, "stable-start"
        )
    async with session_factory() as session:
        replay = await CombatService(CombatUnitOfWork(session)).start(
            player_id, request, "stable-start"
        )
    assert replay == first

    with pytest.raises(GameplayIdempotencyConflict):
        async with session_factory() as session:
            await CombatService(CombatUnitOfWork(session)).start(
                player_id,
                request.model_copy(update={"seed": 405}),
                "stable-start",
            )
    with pytest.raises(CombatConflictError, match="already has"):
        async with session_factory() as session:
            await CombatService(CombatUnitOfWork(session)).start(
                player_id, request, "second-active-start"
            )

    other_player = uuid4()
    other = await _ready_character(other_player)
    with pytest.raises(DefinitionNotFoundError):
        async with session_factory() as session:
            await CombatService(CombatUnitOfWork(session)).start(
                other_player,
                StartCombatRequest(
                    character_id=other.id,
                    encounter_definition_id=uuid4(),
                    seed=1,
                ),
                "missing-definition",
            )

    async with session_factory() as session, session.begin():
        row = await session.get(Character, other.id)
        assert row is not None
        row.current_hp = 0
    with pytest.raises(GameplayRuleViolation, match="recover"):
        async with session_factory() as session:
            await CombatService(CombatUnitOfWork(session)).start(
                other_player,
                StartCombatRequest(
                    character_id=other.id,
                    encounter_definition_id=definition.id,
                    seed=1,
                ),
                "zero-hp-start",
            )


@pytest.mark.asyncio
async def test_invalid_targets_skills_and_items_roll_back(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character = await _ready_character(player_id, "Rogue")
    _, state = await _start(player_id, character.id, 505)
    enemy = next(value for value in state.participants if value.side == "ENEMY")

    invalid_requests = [
        (
            CombatActionRequest(
                combat_id=state.combat_id,
                action_type="ATTACK",
                target_id=uuid4(),
            ),
            "target",
        ),
        (
            CombatActionRequest(combat_id=state.combat_id, action_type="SKILL"),
            "requires a skill",
        ),
        (
            CombatActionRequest(
                combat_id=state.combat_id,
                action_type="SKILL",
                skill_id=uuid4(),
                target_id=enemy.id,
            ),
            "not unlocked",
        ),
        (
            CombatActionRequest(
                combat_id=state.combat_id,
                action_type="SKILL",
                skill_id=character.skills[0].id,
                target_id=enemy.id,
            ),
            "Passive",
        ),
        (
            CombatActionRequest(combat_id=state.combat_id, action_type="ITEM"),
            "requires an inventory item",
        ),
        (
            CombatActionRequest(
                combat_id=state.combat_id,
                action_type="ITEM",
                inventory_item_id=uuid4(),
            ),
            "not found",
        ),
    ]
    for index, (request, message) in enumerate(invalid_requests):
        with pytest.raises(GameplayRuleViolation, match=message):
            await _act(player_id, request, f"invalid-{index}")

    async with session_factory() as session:
        inventory = await CharacterService(GameUnitOfWork(session)).inventory(
            player_id, character.id
        )
    sword = next(value for value in inventory.items if value.item_type == "WEAPON")
    with pytest.raises(GameplayRuleViolation, match="cannot be used"):
        await _act(
            player_id,
            CombatActionRequest(
                combat_id=state.combat_id,
                action_type="ITEM",
                inventory_item_id=sword.inventory_item_id,
            ),
            "invalid-weapon-item",
        )

    async with session_factory() as session, session.begin():
        encounter = await session.get(CombatEncounter, state.combat_id)
        assert encounter is not None
        encounter.action_sequence = 1
    with pytest.raises(CombatConflictError, match="not the player's turn"):
        await _act(
            player_id,
            CombatActionRequest(combat_id=state.combat_id, action_type="WAIT"),
            "out-of-turn",
        )


@pytest.mark.asyncio
async def test_save_create_and_load_are_blocked_during_active_combat(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character = await _ready_character(player_id)
    async with session_factory() as session:
        save = await SaveService(
            SaveUnitOfWork(session), GameStateRepository(session)
        ).create_save(player_id, character.id, "Before combat", "save-before-combat")
    _, state = await _start(player_id, character.id, 606)

    with pytest.raises(SaveActiveCombatError, match="create"):
        async with session_factory() as session:
            await SaveService(
                SaveUnitOfWork(session), GameStateRepository(session)
            ).create_save(
                player_id,
                character.id,
                "During combat",
                "save-during-combat",
            )
    with pytest.raises(SaveActiveCombatError, match="load"):
        async with session_factory() as session:
            await SaveService(
                SaveUnitOfWork(session), GameStateRepository(session)
            ).load_save(player_id, save.save_id, "load-during-combat")

    async with session_factory() as session:
        unchanged = await CombatService(CombatUnitOfWork(session)).get(
            player_id, state.combat_id
        )
    assert unchanged.status == "ACTIVE"
