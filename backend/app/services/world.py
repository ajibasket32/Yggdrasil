import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.metrics import (
    DUNGEON_OPERATIONS_TOTAL,
    NPC_INTERACTIONS_TOTAL,
    QUEST_TRANSITIONS_TOTAL,
    WORLD_EVENTS_TOTAL,
)
from app.engines.character import CharacterEngine, CharacterStats, ProgressionEngine
from app.engines.world import (
    QuestEngine,
    QuestRuleError,
    QuestStatus,
    RelationshipEngine,
)
from app.models.combat import GameOutboxEvent
from app.models.gameplay import Character, CharacterSkill
from app.models.idempotency_record import IdempotencyRecord
from app.models.memory import Memory, MemoryIndexJob
from app.models.world import (
    NPC,
    CharacterDungeonState,
    CharacterFaction,
    CharacterQuest,
    Dungeon,
    Faction,
    JournalEntry,
    Quest,
    Relationship,
    WorldEvent,
)
from app.repositories.world import WorldUnitOfWork
from app.schemas.world import (
    DungeonView,
    FactionView,
    JournalEntryView,
    NPCInteractionResult,
    NPCView,
    QuestStepView,
    QuestView,
    RelationshipView,
    WorldEventView,
    WorldStateView,
)


class WorldError(Exception):
    """Stable error boundary for deterministic v0.7 systems."""

    code = "WORLD_ERROR"
    status_code = 409


class WorldNotFoundError(WorldError):
    code = "WORLD_ENTITY_NOT_FOUND"
    status_code = 404


class WorldRuleViolation(WorldError):
    code = "WORLD_RULE_VIOLATION"
    status_code = 400


class WorldIdempotencyConflict(WorldError):
    code = "IDEMPOTENCY_KEY_REUSED"


class WorldService:
    """Orchestrate deterministic quests, NPCs, factions, and dungeons."""

    def __init__(self, unit_of_work: WorldUnitOfWork) -> None:
        self._uow = unit_of_work
        self._fingerprints: dict[tuple[UUID, str, str], str] = {}

    async def quests(self, player_id: UUID, character_id: UUID) -> list[QuestView]:
        async with self._uow:
            character = await self._character(player_id, character_id)
            rows = await self._uow.world.list_character_quests(player_id, character.id)
            return [
                await self._quest_view(quest, state)
                for quest, state in rows
                if state is not None or quest.location_id == character.current_location_id
            ]

    async def accept_quest(
        self, player_id: UUID, character_id: UUID, quest_id: UUID, key: str
    ) -> QuestView:
        operation = "quest.accept"
        async with self._uow:
            existing = await self._guard(
                player_id,
                key,
                operation,
                {"character_id": character_id, "quest_id": quest_id},
            )
            character = await self._character(player_id, character_id, for_update=True)
            quest = await self._quest(quest_id)
            if existing is not None:
                return await self._quest_view(
                    quest,
                    await self._uow.world.get_character_quest(character.id, quest.id),
                )
            if quest.location_id != character.current_location_id:
                raise WorldRuleViolation("Quest is not available at this location")
            state = await self._uow.world.get_character_quest(
                character.id, quest.id, for_update=True
            )
            if state is None:
                state = CharacterQuest(
                    player_id=player_id,
                    character_id=character.id,
                    quest_id=quest.id,
                )
                await self._uow.world.add(state)
            try:
                QuestEngine.validate_acceptance(
                    character.level,
                    quest.minimum_level,
                    await self._prerequisites_complete(character.id, quest),
                )
                state.status = QuestEngine.transition(
                    state.status, QuestStatus.ACTIVE
                ).current.value
            except QuestRuleError as error:
                raise WorldRuleViolation(str(error)) from error
            state.accepted_at = datetime.now(UTC)
            await self._journal(
                player_id,
                character.id,
                quest,
                "QUEST_ACCEPTED",
                f"Accepted {quest.title}.",
            )
            await self._outbox(player_id, "quest.accepted", "quest", quest.id, character.id, key)
            await self._record(player_id, key, operation, character.id)
            QUEST_TRANSITIONS_TOTAL.labels("NOT_STARTED", "ACTIVE", "success").inc()
            return await self._quest_view(quest, state)

    async def fail_quest(
        self, player_id: UUID, character_id: UUID, quest_id: UUID, key: str
    ) -> QuestView:
        return await self._transition_terminal(
            player_id, character_id, quest_id, key, QuestStatus.FAILED
        )

    async def archive_quest(
        self, player_id: UUID, character_id: UUID, quest_id: UUID, key: str
    ) -> QuestView:
        operation = "quest.archive"
        async with self._uow:
            existing = await self._guard(
                player_id,
                key,
                operation,
                {"character_id": character_id, "quest_id": quest_id},
            )
            character = await self._character(player_id, character_id)
            quest = await self._quest(quest_id)
            state = await self._state(character.id, quest.id, for_update=True)
            if existing is None:
                previous = state.status
                try:
                    state.status = QuestEngine.transition(
                        state.status, QuestStatus.ARCHIVED
                    ).current.value
                except QuestRuleError as error:
                    raise WorldRuleViolation(str(error)) from error
                state.archived_at = datetime.now(UTC)
                await self._record(player_id, key, operation, character.id)
                QUEST_TRANSITIONS_TOTAL.labels(previous, "ARCHIVED", "success").inc()
            return await self._quest_view(quest, state)

    async def submit_quest(
        self, player_id: UUID, character_id: UUID, quest_id: UUID, key: str
    ) -> QuestView:
        operation = "quest.submit"
        async with self._uow:
            existing = await self._guard(
                player_id,
                key,
                operation,
                {"character_id": character_id, "quest_id": quest_id},
            )
            character = await self._character(player_id, character_id, for_update=True)
            quest = await self._quest(quest_id)
            state = await self._state(character.id, quest.id, for_update=True)
            if existing is not None:
                return await self._quest_view(quest, state)
            if not state.objectives_complete:
                raise WorldRuleViolation("Quest objectives are not complete")
            try:
                experience, gold, reputation = QuestEngine.rewards(quest.rewards)
                state.status = QuestEngine.transition(
                    state.status, QuestStatus.COMPLETED
                ).current.value
            except QuestRuleError as error:
                raise WorldRuleViolation(str(error)) from error
            await self._apply_progression(character, experience)
            character.gold += gold
            state.rewards_claimed = True
            state.completed_at = datetime.now(UTC)
            if quest.faction_id is not None:
                standing = await self._standing(player_id, character.id, quest.faction_id)
                standing.reputation = min(1000, standing.reputation + reputation)
                standing.rank = self._rank(standing.reputation, standing.joined)
            await self._journal(
                player_id,
                character.id,
                quest,
                "QUEST_COMPLETED",
                f"Completed {quest.title}. Rewards: {experience} XP and {gold} gold.",
            )
            event = await self._world_event(
                player_id,
                character,
                "QUEST_COMPLETED",
                f"quest:{quest.id}:completed",
                quest=quest,
                payload={"experience": experience, "gold": gold},
            )
            await self._memory(
                player_id,
                character,
                "QUEST_MEMORY",
                "quest",
                quest.id,
                f"{character.name} completed {quest.title}.",
                7,
                event,
                ("quest", "completed"),
            )
            await self._outbox(player_id, "quest.completed", "quest", quest.id, character.id, key)
            await self._record(player_id, key, operation, character.id)
            QUEST_TRANSITIONS_TOTAL.labels("ACTIVE", "COMPLETED", "success").inc()
            return await self._quest_view(quest, state)

    async def npcs(self, player_id: UUID, character_id: UUID) -> list[NPCView]:
        async with self._uow:
            character = await self._character(player_id, character_id)
            return [
                self._npc_view(value, character.current_location_id)
                for value in await self._uow.world.list_npcs(character.current_location_id)
            ]

    async def relationship(
        self, player_id: UUID, character_id: UUID, npc_id: UUID
    ) -> RelationshipView:
        async with self._uow:
            await self._character(player_id, character_id)
            await self._npc(npc_id)
            row = await self._relationship_row(player_id, character_id, npc_id)
            return RelationshipView.model_validate(row)

    async def interact(
        self,
        player_id: UUID,
        character_id: UUID,
        npc_id: UUID,
        action_id: str,
        key: str,
    ) -> NPCInteractionResult:
        operation = f"npc.interact.{action_id.lower()}"
        async with self._uow:
            existing = await self._guard(
                player_id,
                key,
                operation,
                {
                    "character_id": character_id,
                    "npc_id": npc_id,
                    "action_id": action_id,
                },
            )
            character = await self._character(player_id, character_id)
            npc = await self._npc(npc_id)
            if npc.home_location_id != character.current_location_id:
                raise WorldRuleViolation("NPC is not at the character's location")
            relationship = await self._relationship_row(
                player_id, character.id, npc.id, for_update=True
            )
            progressed = False
            if existing is None and action_id == "OFFER_HELP":
                memory_created = await self._memory(
                    player_id,
                    character,
                    "NPC_MEMORY",
                    "npc",
                    npc.id,
                    f"{character.name} offered practical aid to {npc.name}.",
                    5,
                    None,
                    ("npc", "help"),
                )
                if memory_created:
                    self._apply_relationship(
                        relationship, {"trust": 5, "friendship": 2, "respect": 3}
                    )
                    progressed = await self._progress_matching(
                        player_id, character, "NPC_HELP", npc.id
                    )
                    await self._outbox(
                        player_id,
                        "npc.relationship_changed",
                        "npc",
                        npc.id,
                        character.id,
                        key,
                    )
            if existing is None:
                await self._record(player_id, key, operation, character.id)
                NPC_INTERACTIONS_TOTAL.labels(action_id, "success").inc()
            text = (
                f"{npc.name} acknowledges the offer and records the aid."
                if action_id == "OFFER_HELP"
                else f"{npc.name} offers a brief, practical greeting."
            )
            return NPCInteractionResult(
                npc=self._npc_view(npc, character.current_location_id),
                relationship=RelationshipView.model_validate(relationship),
                action_id=action_id,
                result_text=text,
                quest_progressed=progressed,
            )

    async def factions(self, player_id: UUID, character_id: UUID) -> list[FactionView]:
        async with self._uow:
            await self._character(player_id, character_id)
            return [
                await self._faction_view(player_id, character_id, faction)
                for faction in await self._uow.world.list_factions()
            ]

    async def join_faction(
        self, player_id: UUID, character_id: UUID, faction_id: UUID, key: str
    ) -> FactionView:
        operation = "faction.join"
        async with self._uow:
            existing = await self._guard(
                player_id,
                key,
                operation,
                {"character_id": character_id, "faction_id": faction_id},
            )
            character = await self._character(player_id, character_id)
            faction = await self._faction(faction_id)
            standing = await self._standing(player_id, character.id, faction.id)
            if existing is None:
                if standing.joined:
                    raise WorldRuleViolation("Character already joined this faction")
                standing.joined = True
                standing.rank = self._rank(standing.reputation, True)
                event = await self._world_event(
                    player_id,
                    character,
                    "FACTION_JOINED",
                    f"faction:{faction.id}:joined",
                    faction=faction,
                    payload={"rank": standing.rank},
                )
                await self._memory(
                    player_id,
                    character,
                    "FACTION_MEMORY",
                    "faction",
                    faction.id,
                    f"{character.name} joined {faction.name}.",
                    7,
                    event,
                    ("faction", "joined"),
                )
                await self._outbox(
                    player_id,
                    "world.faction_joined",
                    "faction",
                    faction.id,
                    character.id,
                    key,
                )
                await self._record(player_id, key, operation, character.id)
            return self._faction_view_from(faction, standing)

    async def dungeons(self, player_id: UUID, character_id: UUID) -> list[DungeonView]:
        async with self._uow:
            character = await self._character(player_id, character_id)
            return [
                await self._dungeon_view(player_id, character.id, dungeon)
                for dungeon in await self._uow.world.list_dungeons()
                if dungeon.location_id == character.current_location_id
                or await self._uow.world.get_dungeon_state(character.id, dungeon.id) is not None
            ]

    async def enter_dungeon(
        self, player_id: UUID, character_id: UUID, dungeon_id: UUID, key: str
    ) -> DungeonView:
        return await self._mutate_dungeon(player_id, character_id, dungeon_id, key, clear=False)

    async def clear_dungeon(
        self, player_id: UUID, character_id: UUID, dungeon_id: UUID, key: str
    ) -> DungeonView:
        return await self._mutate_dungeon(player_id, character_id, dungeon_id, key, clear=True)

    async def journal(self, player_id: UUID, character_id: UUID) -> list[JournalEntryView]:
        async with self._uow:
            await self._character(player_id, character_id)
            return [
                JournalEntryView.model_validate(value)
                for value in await self._uow.world.list_journal(character_id)
            ]

    async def state(self, player_id: UUID, character_id: UUID) -> WorldStateView:
        async with self._uow:
            character = await self._character(player_id, character_id)
            return WorldStateView(
                world_tick=0,
                npcs=[
                    self._npc_view(value, character.current_location_id)
                    for value in await self._uow.world.list_npcs(character.current_location_id)
                ],
                factions=[
                    await self._faction_view(player_id, character.id, faction)
                    for faction in await self._uow.world.list_factions()
                ],
                dungeons=[
                    await self._dungeon_view(player_id, character.id, dungeon)
                    for dungeon in await self._uow.world.list_dungeons()
                ],
                active_world_events=[
                    WorldEventView.model_validate(value)
                    for value in await self._uow.world.list_events(character.id)
                ],
            )

    async def _transition_terminal(
        self,
        player_id: UUID,
        character_id: UUID,
        quest_id: UUID,
        key: str,
        target: QuestStatus,
    ) -> QuestView:
        operation = f"quest.{target.value.lower()}"
        async with self._uow:
            existing = await self._guard(
                player_id,
                key,
                operation,
                {"character_id": character_id, "quest_id": quest_id},
            )
            character = await self._character(player_id, character_id)
            quest = await self._quest(quest_id)
            state = await self._state(character.id, quest.id, for_update=True)
            if existing is None:
                previous = state.status
                try:
                    state.status = QuestEngine.transition(state.status, target).current.value
                except QuestRuleError as error:
                    raise WorldRuleViolation(str(error)) from error
                await self._journal(
                    player_id,
                    character.id,
                    quest,
                    f"QUEST_{target.value}",
                    f"{quest.title} is now {target.value.lower()}.",
                )
                await self._outbox(
                    player_id,
                    f"quest.{target.value.lower()}",
                    "quest",
                    quest.id,
                    character.id,
                    key,
                )
                await self._record(player_id, key, operation, character.id)
                QUEST_TRANSITIONS_TOTAL.labels(previous, target.value, "success").inc()
            return await self._quest_view(quest, state)

    async def _mutate_dungeon(
        self,
        player_id: UUID,
        character_id: UUID,
        dungeon_id: UUID,
        key: str,
        *,
        clear: bool,
    ) -> DungeonView:
        operation = "dungeon.clear" if clear else "dungeon.enter"
        async with self._uow:
            existing = await self._guard(
                player_id,
                key,
                operation,
                {"character_id": character_id, "dungeon_id": dungeon_id},
            )
            character = await self._character(player_id, character_id)
            dungeon = await self._dungeon(dungeon_id)
            if dungeon.location_id != character.current_location_id:
                raise WorldRuleViolation("Dungeon is not at the character's location")
            state = await self._uow.world.get_dungeon_state(
                character.id, dungeon.id, for_update=True
            )
            if state is None:
                state = CharacterDungeonState(
                    player_id=player_id,
                    character_id=character.id,
                    dungeon_id=dungeon.id,
                )
                await self._uow.world.add(state)
            if existing is None:
                state.entered = True
                if clear and not state.cleared:
                    if character.level < dungeon.recommended_level:
                        raise WorldRuleViolation("Character level is below dungeon recommendation")
                    state.cleared = True
                    state.boss_alive = False
                    state.cleared_at = datetime.now(UTC)
                    await self._progress_matching(player_id, character, "DUNGEON_CLEAR", dungeon.id)
                    event = await self._world_event(
                        player_id,
                        character,
                        "DUNGEON_CLEARED",
                        f"dungeon:{dungeon.id}:cleared",
                        payload={"dungeon_id": str(dungeon.id)},
                    )
                    await self._memory(
                        player_id,
                        character,
                        "WORLD_MEMORY",
                        "dungeon",
                        dungeon.id,
                        f"{character.name} permanently cleared {dungeon.name}.",
                        8,
                        event,
                        ("dungeon", "cleared"),
                    )
                    await self._outbox(
                        player_id,
                        "world.dungeon_cleared",
                        "dungeon",
                        dungeon.id,
                        character.id,
                        key,
                    )
                await self._record(player_id, key, operation, character.id)
                DUNGEON_OPERATIONS_TOTAL.labels("clear" if clear else "enter", "success").inc()
            return self._dungeon_view_from(dungeon, state)

    async def _progress_matching(
        self,
        player_id: UUID,
        character: Character,
        objective_type: str,
        target_id: UUID,
    ) -> bool:
        for quest, state in await self._uow.world.list_character_quests(player_id, character.id):
            if state is None or state.status != "ACTIVE" or state.objectives_complete:
                continue
            steps = await self._uow.world.list_steps(quest.id)
            if state.current_step >= len(steps):
                continue
            step = steps[state.current_step]
            if step.objective_type != objective_type or step.target_id != target_id:
                continue
            try:
                state.current_step, state.step_progress, state.objectives_complete = (
                    QuestEngine.advance_step(
                        state.current_step,
                        len(steps),
                        state.step_progress,
                        step.required_count,
                    )
                )
            except QuestRuleError as error:
                raise WorldRuleViolation(str(error)) from error
            await self._journal(
                player_id,
                character.id,
                quest,
                "QUEST_PROGRESS",
                f"Objective complete: {step.description}",
            )
            await self._outbox(
                player_id,
                "quest.step_completed",
                "quest",
                quest.id,
                character.id,
                f"{quest.id}:{step.sequence}",
            )
            return True
        return False

    async def _apply_progression(self, character: Character, amount: int) -> None:
        row = await self._uow.world.active_job(character)
        if row is None:
            raise WorldRuleViolation("Active job progression is missing")
        character_job, job = row
        unlocks = await self._uow.world.job_skills(job.id)
        result = ProgressionEngine.award_experience(
            level=character.level,
            experience=character.experience,
            job_level=character_job.job_level,
            job_experience=character_job.experience,
            job_max_level=job.max_level,
            skill_points=character.skill_points,
            stats=self._stats(character),
            job_stat_modifiers=job.stat_modifiers,
            skill_unlocks=[(value.skill_id, value.required_level) for value in unlocks],
            already_unlocked=await self._uow.world.skill_ids(character.id),
            amount=amount,
        )
        character.level = result.level
        character.experience = result.experience
        character.skill_points = result.skill_points
        for name, value in result.stats.as_dict().items():
            setattr(character, name, value)
        character_job.job_level = result.job_level
        character_job.experience = result.job_experience
        for skill_id in result.unlocked_skill_ids:
            await self._uow.world.add(
                CharacterSkill(character_id=character.id, skill_id=skill_id, skill_level=1)
            )
        derived = CharacterEngine.derive(result.stats)
        character.current_hp = derived.max_hp
        character.current_mp = derived.max_mp
        character.current_stamina = derived.max_stamina

    async def _quest_view(self, quest: Quest, state: CharacterQuest | None) -> QuestView:
        steps = await self._uow.world.list_steps(quest.id)
        current_step = state.current_step if state else 0
        progress = state.step_progress if state else 0
        rewards = QuestEngine.rewards(quest.rewards)
        return QuestView(
            id=quest.id,
            title=quest.title,
            description=quest.description,
            minimum_level=quest.minimum_level,
            status=state.status if state else "NOT_STARTED",
            objectives_complete=state.objectives_complete if state else False,
            rewards_claimed=state.rewards_claimed if state else False,
            current_step=current_step,
            steps=[
                QuestStepView(
                    id=step.id,
                    sequence=step.sequence,
                    objective_type=step.objective_type,
                    target_id=step.target_id,
                    description=step.description,
                    required_count=step.required_count,
                    progress=(
                        step.required_count
                        if state and step.sequence < current_step
                        else progress
                        if state and step.sequence == current_step
                        else 0
                    ),
                    complete=bool(
                        state
                        and (
                            step.sequence < current_step
                            or state.objectives_complete
                            and step.sequence == len(steps) - 1
                        )
                    ),
                )
                for step in steps
            ],
            rewards={
                "experience": rewards[0],
                "gold": rewards[1],
                "reputation": rewards[2],
            },
        )

    async def _guard(
        self,
        player_id: UUID,
        key: str,
        operation: str,
        payload: dict[str, object],
    ) -> IdempotencyRecord | None:
        await self._uow.lock_key(f"idempotency:{player_id}:{operation}:{key}")
        fingerprint = self._fingerprint(payload)
        self._fingerprints[(player_id, key, operation)] = fingerprint
        existing = await self._uow.idempotency.get(player_id, key, operation)
        if existing and existing.request_fingerprint != fingerprint:
            raise WorldIdempotencyConflict(
                "Idempotency key was already used with a different request"
            )
        return existing

    async def _record(self, player_id: UUID, key: str, operation: str, character_id: UUID) -> None:
        await self._uow.idempotency.add(
            IdempotencyRecord(
                player_id=player_id,
                idempotency_key=key,
                request_fingerprint=self._fingerprints[(player_id, key, operation)],
                operation=operation,
                response_status=200,
                response_body={"character_id": str(character_id)},
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )

    async def _character(
        self, player_id: UUID, character_id: UUID, *, for_update: bool = False
    ) -> Character:
        value = await self._uow.world.get_character(player_id, character_id, for_update=for_update)
        if value is None:
            raise WorldNotFoundError("Character was not found")
        return value

    async def _quest(self, quest_id: UUID) -> Quest:
        value = await self._uow.world.get_quest(quest_id)
        if value is None:
            raise WorldNotFoundError("Quest was not found")
        return value

    async def _state(
        self, character_id: UUID, quest_id: UUID, *, for_update: bool = False
    ) -> CharacterQuest:
        value = await self._uow.world.get_character_quest(
            character_id, quest_id, for_update=for_update
        )
        if value is None:
            raise WorldRuleViolation("Quest has not been accepted")
        return value

    async def _npc(self, npc_id: UUID) -> NPC:
        value = await self._uow.world.get_npc(npc_id)
        if value is None or not value.is_alive:
            raise WorldNotFoundError("NPC was not found")
        return value

    async def _faction(self, faction_id: UUID) -> Faction:
        value = await self._uow.world.get_faction(faction_id)
        if value is None:
            raise WorldNotFoundError("Faction was not found")
        return value

    async def _dungeon(self, dungeon_id: UUID) -> Dungeon:
        value = await self._uow.world.get_dungeon(dungeon_id)
        if value is None:
            raise WorldNotFoundError("Dungeon was not found")
        return value

    async def _relationship_row(
        self,
        player_id: UUID,
        character_id: UUID,
        npc_id: UUID,
        *,
        for_update: bool = False,
    ) -> Relationship:
        value = await self._uow.world.get_relationship(character_id, npc_id, for_update=for_update)
        if value is None:
            value = Relationship(player_id=player_id, character_id=character_id, npc_id=npc_id)
            await self._uow.world.add(value)
        return value

    async def _standing(
        self, player_id: UUID, character_id: UUID, faction_id: UUID
    ) -> CharacterFaction:
        value = await self._uow.world.get_character_faction(
            character_id, faction_id, for_update=True
        )
        if value is None:
            value = CharacterFaction(
                player_id=player_id,
                character_id=character_id,
                faction_id=faction_id,
            )
            await self._uow.world.add(value)
        return value

    async def _faction_view(
        self, player_id: UUID, character_id: UUID, faction: Faction
    ) -> FactionView:
        standing = await self._uow.world.get_character_faction(character_id, faction.id)
        if standing is None:
            standing = CharacterFaction(
                player_id=player_id,
                character_id=character_id,
                faction_id=faction.id,
                reputation=0,
                rank="OUTSIDER",
                joined=False,
            )
        return self._faction_view_from(faction, standing)

    async def _dungeon_view(
        self, player_id: UUID, character_id: UUID, dungeon: Dungeon
    ) -> DungeonView:
        state = await self._uow.world.get_dungeon_state(character_id, dungeon.id)
        if state is None:
            state = CharacterDungeonState(
                player_id=player_id,
                character_id=character_id,
                dungeon_id=dungeon.id,
                entered=False,
                cleared=False,
                boss_alive=True,
            )
        return self._dungeon_view_from(dungeon, state)

    async def _prerequisites_complete(self, character_id: UUID, quest: Quest) -> bool:
        for value in quest.prerequisites:
            state = await self._uow.world.get_character_quest(character_id, UUID(str(value)))
            if state is None or state.status not in {"COMPLETED", "ARCHIVED"}:
                return False
        return True

    async def _journal(
        self,
        player_id: UUID,
        character_id: UUID,
        quest: Quest,
        category: str,
        body: str,
    ) -> None:
        await self._uow.world.add(
            JournalEntry(
                player_id=player_id,
                character_id=character_id,
                quest_id=quest.id,
                category=category,
                title=quest.title,
                body=body,
            )
        )

    async def _world_event(
        self,
        player_id: UUID,
        character: Character,
        event_type: str,
        suffix: str,
        *,
        quest: Quest | None = None,
        faction: Faction | None = None,
        payload: dict[str, object],
    ) -> WorldEvent:
        event = WorldEvent(
            player_id=player_id,
            character_id=character.id,
            event_type=event_type,
            location_id=character.current_location_id,
            faction_id=faction.id if faction else quest.faction_id if quest else None,
            quest_id=quest.id if quest else None,
            payload=payload,
            deduplication_key=f"{player_id}:{character.id}:{suffix}",
        )
        await self._uow.world.add(event)
        WORLD_EVENTS_TOTAL.labels(event_type, "created").inc()
        return event

    async def _memory(
        self,
        player_id: UUID,
        character: Character,
        memory_type: str,
        entity_type: str,
        entity_id: UUID,
        summary: str,
        importance: int,
        world_event: WorldEvent | None,
        tags: tuple[str, ...],
    ) -> bool:
        content_hash = hashlib.sha256(
            f"{memory_type}:{entity_type}:{entity_id}:{summary.casefold()}".encode()
        ).hexdigest()
        existing = await self._uow.world.get_active_memory(
            player_id, memory_type, entity_type, entity_id, content_hash
        )
        if existing is not None:
            return False
        memory = Memory(
            player_id=player_id,
            memory_type=memory_type,
            source_entity_type="character",
            source_entity_id=character.id,
            summary=summary,
            importance=importance,
            world_event_id=world_event.id if world_event else None,
            entity_id=entity_id,
            entity_type=entity_type,
            participants=[str(character.id)],
            location_id=character.current_location_id,
            tags=list(tags),
            occurred_at=datetime.now(UTC),
            content_hash=content_hash,
            version=1,
            status="ACTIVE",
            index_status="PENDING",
        )
        await self._uow.world.add(memory)
        await self._uow.world.add(
            MemoryIndexJob(
                memory_id=memory.id,
                operation="UPSERT",
                status="PENDING",
                attempts=0,
                max_attempts=5,
                next_attempt_at=datetime.now(UTC),
            )
        )
        return True

    async def _outbox(
        self,
        player_id: UUID,
        event_type: str,
        aggregate_type: str,
        aggregate_id: UUID,
        character_id: UUID,
        suffix: str,
    ) -> None:
        await self._uow.world.add(
            GameOutboxEvent(
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                player_id=player_id,
                payload={"character_id": str(character_id)},
                deduplication_key=f"{event_type}:{aggregate_id}:{character_id}:{suffix}",
            )
        )

    @staticmethod
    def _apply_relationship(relationship: Relationship, deltas: dict[str, int]) -> None:
        values = RelationshipEngine.apply(
            {field: int(getattr(relationship, field)) for field in RelationshipEngine.FIELDS},
            deltas,
        )
        for field, value in values.items():
            setattr(relationship, field, value)

    @staticmethod
    def _npc_view(npc: NPC, current_location_id: UUID) -> NPCView:
        return NPCView(
            id=npc.id,
            name=npc.name,
            occupation=npc.occupation,
            role=npc.role,
            faction_id=npc.faction_id,
            current_location_id=npc.home_location_id,
            personality_profile=npc.personality_profile,
            knowledge=npc.knowledge,
            is_alive=npc.is_alive,
            available_actions=(
                ["GREET", "OFFER_HELP"] if npc.home_location_id == current_location_id else []
            ),
        )

    @staticmethod
    def _faction_view_from(faction: Faction, standing: CharacterFaction) -> FactionView:
        return FactionView(
            id=faction.id,
            name=faction.name,
            description=faction.description,
            reputation=standing.reputation,
            rank=standing.rank,
            joined=standing.joined,
        )

    @staticmethod
    def _dungeon_view_from(dungeon: Dungeon, state: CharacterDungeonState) -> DungeonView:
        return DungeonView(
            id=dungeon.id,
            name=dungeon.name,
            description=dungeon.description,
            location_id=dungeon.location_id,
            recommended_level=dungeon.recommended_level,
            entered=state.entered,
            cleared=state.cleared,
            boss_alive=state.boss_alive,
        )

    @staticmethod
    def _rank(reputation: int, joined: bool) -> str:
        if not joined:
            return "OUTSIDER"
        if reputation >= 100:
            return "WARDEN"
        if reputation >= 25:
            return "ALLY"
        return "INITIATE"

    @staticmethod
    def _stats(character: Character) -> CharacterStats:
        return CharacterStats(
            strength=character.strength,
            dexterity=character.dexterity,
            agility=character.agility,
            vitality=character.vitality,
            intelligence=character.intelligence,
            wisdom=character.wisdom,
            charisma=character.charisma,
        )

    @staticmethod
    def _fingerprint(payload: dict[str, object]) -> str:
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
