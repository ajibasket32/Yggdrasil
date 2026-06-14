from dataclasses import dataclass
from types import TracebackType
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.models.gameplay import Character, Location
from app.models.memory import Memory
from app.models.narrative import NarrativeRecord
from app.models.world import (
    NPC,
    CharacterFaction,
    CharacterQuest,
    Faction,
    Quest,
    QuestStep,
    Relationship,
)


@dataclass(frozen=True)
class QuestContextRow:
    quest: Quest
    state: CharacterQuest | None
    current_step: QuestStep | None


class NarrativeRepository:
    """Read canonical context and store validated cosmetic narrative."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_character(
        self, player_id: UUID, character_id: UUID
    ) -> Character | None:
        result = await self._session.execute(
            select(Character).where(
                Character.id == character_id,
                Character.player_id == player_id,
                Character.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_location(self, location_id: UUID) -> Location | None:
        return await self._session.get(Location, location_id)

    async def get_npc(self, npc_id: UUID) -> NPC | None:
        return await self._session.get(NPC, npc_id)

    async def get_faction(self, faction_id: UUID) -> Faction | None:
        return await self._session.get(Faction, faction_id)

    async def get_relationship(
        self, character_id: UUID, npc_id: UUID
    ) -> Relationship | None:
        result = await self._session.execute(
            select(Relationship).where(
                Relationship.character_id == character_id,
                Relationship.npc_id == npc_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_faction_standing(
        self, character_id: UUID, faction_id: UUID
    ) -> CharacterFaction | None:
        result = await self._session.execute(
            select(CharacterFaction).where(
                CharacterFaction.character_id == character_id,
                CharacterFaction.faction_id == faction_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_quest(self, quest_id: UUID) -> Quest | None:
        return await self._session.get(Quest, quest_id)

    async def list_quest_context(
        self, character_id: UUID, location_id: UUID
    ) -> list[QuestContextRow]:
        quests = list(
            (
                await self._session.execute(
                    select(Quest).where(Quest.location_id == location_id)
                )
            )
            .scalars()
            .all()
        )
        states = list(
            (
                await self._session.execute(
                    select(CharacterQuest).where(
                        CharacterQuest.character_id == character_id
                    )
                )
            )
            .scalars()
            .all()
        )
        state_by_quest = {value.quest_id: value for value in states}
        known_ids = set(state_by_quest)
        existing_ids = {value.id for value in quests}
        if known_ids:
            known_quests = list(
                (
                    await self._session.execute(
                        select(Quest).where(Quest.id.in_(known_ids))
                    )
                )
                .scalars()
                .all()
            )
            quests.extend(
                quest for quest in known_quests if quest.id not in existing_ids
            )
        active_steps = {
            (state.quest_id, state.current_step)
            for state in states
            if not state.objectives_complete
        }
        step_by_quest = {}
        if active_steps:
            quest_ids = {quest_id for quest_id, _ in active_steps}
            sequences = {sequence for _, sequence in active_steps}
            steps = (
                (
                    await self._session.execute(
                        select(QuestStep).where(
                            QuestStep.quest_id.in_(quest_ids),
                            QuestStep.sequence.in_(sequences),
                        )
                    )
                )
                .scalars()
                .all()
            )
            step_by_quest = {
                step.quest_id: step
                for step in steps
                if (step.quest_id, step.sequence) in active_steps
            }
        rows: list[QuestContextRow] = []
        for quest in sorted(quests, key=lambda value: (value.title, str(value.id))):
            state = state_by_quest.get(quest.id)
            current_step = step_by_quest.get(quest.id)
            rows.append(QuestContextRow(quest, state, current_step))
        return rows

    async def list_context_memories(
        self,
        player_id: UUID,
        character_id: UUID,
        *,
        memory_ids: list[UUID] | None = None,
        limit: int = 20,
    ) -> list[Memory]:
        statement = (
            select(Memory)
            .where(
                Memory.player_id == player_id,
                Memory.source_entity_id == character_id,
                Memory.deleted_at.is_(None),
                Memory.status == "ACTIVE",
            )
            .order_by(Memory.importance.desc(), Memory.occurred_at.desc(), Memory.id)
            .limit(limit)
        )
        if memory_ids is not None:
            if not memory_ids:
                return []
            statement = statement.where(Memory.id.in_(memory_ids))
        return list((await self._session.execute(statement)).scalars().all())

    async def recent_dialogue(
        self, player_id: UUID, character_id: UUID, npc_id: UUID, limit: int = 10
    ) -> list[NarrativeRecord]:
        result = await self._session.execute(
            select(NarrativeRecord)
            .where(
                NarrativeRecord.player_id == player_id,
                NarrativeRecord.character_id == character_id,
                NarrativeRecord.npc_id == npc_id,
                NarrativeRecord.kind == "dialogue",
            )
            .order_by(NarrativeRecord.created_at.desc(), NarrativeRecord.id.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

    async def find_cached(
        self,
        player_id: UUID,
        character_id: UUID,
        kind: str,
        entity_id: UUID,
        topic_id: str,
        prompt_version: str,
        context_hash: str,
    ) -> NarrativeRecord | None:
        result = await self._session.execute(
            select(NarrativeRecord)
            .where(
                NarrativeRecord.player_id == player_id,
                NarrativeRecord.character_id == character_id,
                NarrativeRecord.kind == kind,
                NarrativeRecord.entity_id == entity_id,
                NarrativeRecord.topic_id == topic_id,
                NarrativeRecord.prompt_version == prompt_version,
                NarrativeRecord.context_hash == context_hash,
            )
            .order_by(NarrativeRecord.created_at.desc(), NarrativeRecord.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_request(
        self, player_id: UUID, kind: str, request_key: str
    ) -> NarrativeRecord | None:
        result = await self._session.execute(
            select(NarrativeRecord).where(
                NarrativeRecord.player_id == player_id,
                NarrativeRecord.kind == kind,
                NarrativeRecord.request_key == request_key,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, record: NarrativeRecord) -> NarrativeRecord:
        self._session.add(record)
        await self._session.flush()
        return record


class NarrativeUnitOfWork:
    """Own one short transaction for narrative context or storage."""

    def __init__(self, session: AsyncSession) -> None:
        self.narrative = NarrativeRepository(session)
        self._session = session
        self._transaction: AsyncSessionTransaction | None = None

    async def __aenter__(self) -> "NarrativeUnitOfWork":
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._transaction is None:
            raise RuntimeError("NarrativeUnitOfWork exited before it was entered")
        await self._transaction.__aexit__(exc_type, exc_value, traceback)
