from dataclasses import dataclass
from types import TracebackType
from uuid import UUID

from pydantic import JsonValue
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.models.gameplay import Character, CharacterJob, CharacterSkill, Job, JobSkill
from app.models.memory import Memory
from app.models.world import (
    NPC,
    CharacterDungeonState,
    CharacterFaction,
    CharacterQuest,
    Dungeon,
    Faction,
    JournalEntry,
    Quest,
    QuestStep,
    Relationship,
    WorldEvent,
)
from app.repositories.save import IdempotencyRepository


@dataclass(frozen=True)
class WorldSnapshot:
    quest_state: dict[str, JsonValue]
    npc_state: dict[str, JsonValue]
    faction_state: dict[str, JsonValue]
    relationships: dict[str, JsonValue]
    journal: dict[str, JsonValue]
    memories: dict[str, JsonValue]
    dungeon_state: dict[str, JsonValue]


class WorldRepository:
    """Player-scoped persistence for deterministic v0.7 world systems."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_character(
        self, player_id: UUID, character_id: UUID, *, for_update: bool = False
    ) -> Character | None:
        statement = select(Character).where(
            Character.id == character_id,
            Character.player_id == player_id,
            Character.deleted_at.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def list_quests(self, location_id: UUID | None = None) -> list[Quest]:
        statement = select(Quest).order_by(Quest.title)
        if location_id is not None:
            statement = statement.where(Quest.location_id == location_id)
        return list((await self._session.execute(statement)).scalars().all())

    async def get_quest(self, quest_id: UUID) -> Quest | None:
        return await self._session.get(Quest, quest_id)

    async def list_steps(self, quest_id: UUID) -> list[QuestStep]:
        result = await self._session.execute(
            select(QuestStep)
            .where(QuestStep.quest_id == quest_id)
            .order_by(QuestStep.sequence)
        )
        return list(result.scalars().all())

    async def get_character_quest(
        self, character_id: UUID, quest_id: UUID, *, for_update: bool = False
    ) -> CharacterQuest | None:
        statement = select(CharacterQuest).where(
            CharacterQuest.character_id == character_id,
            CharacterQuest.quest_id == quest_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def list_character_quests(
        self, player_id: UUID, character_id: UUID
    ) -> list[tuple[Quest, CharacterQuest | None]]:
        quests = await self.list_quests()
        return [
            (quest, await self.get_character_quest(character_id, quest.id))
            for quest in quests
        ]

    async def add(self, value: object) -> None:
        self._session.add(value)
        await self._session.flush()

    async def list_npcs(self, location_id: UUID) -> list[NPC]:
        result = await self._session.execute(
            select(NPC).where(
                NPC.home_location_id == location_id, NPC.is_alive.is_(True)
            )
        )
        return list(result.scalars().all())

    async def get_npc(self, npc_id: UUID) -> NPC | None:
        return await self._session.get(NPC, npc_id)

    async def get_relationship(
        self, character_id: UUID, npc_id: UUID, *, for_update: bool = False
    ) -> Relationship | None:
        statement = select(Relationship).where(
            Relationship.character_id == character_id,
            Relationship.npc_id == npc_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def list_relationships(self, character_id: UUID) -> list[Relationship]:
        result = await self._session.execute(
            select(Relationship).where(Relationship.character_id == character_id)
        )
        return list(result.scalars().all())

    async def list_factions(self) -> list[Faction]:
        return list(
            (
                await self._session.execute(select(Faction).order_by(Faction.name))
            ).scalars()
        )

    async def get_faction(self, faction_id: UUID) -> Faction | None:
        return await self._session.get(Faction, faction_id)

    async def get_character_faction(
        self, character_id: UUID, faction_id: UUID, *, for_update: bool = False
    ) -> CharacterFaction | None:
        statement = select(CharacterFaction).where(
            CharacterFaction.character_id == character_id,
            CharacterFaction.faction_id == faction_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def list_character_factions(
        self, character_id: UUID
    ) -> list[CharacterFaction]:
        result = await self._session.execute(
            select(CharacterFaction).where(
                CharacterFaction.character_id == character_id
            )
        )
        return list(result.scalars().all())

    async def list_dungeons(self) -> list[Dungeon]:
        return list(
            (
                await self._session.execute(select(Dungeon).order_by(Dungeon.name))
            ).scalars()
        )

    async def get_dungeon(self, dungeon_id: UUID) -> Dungeon | None:
        return await self._session.get(Dungeon, dungeon_id)

    async def get_dungeon_state(
        self, character_id: UUID, dungeon_id: UUID, *, for_update: bool = False
    ) -> CharacterDungeonState | None:
        statement = select(CharacterDungeonState).where(
            CharacterDungeonState.character_id == character_id,
            CharacterDungeonState.dungeon_id == dungeon_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def list_dungeon_states(
        self, character_id: UUID
    ) -> list[CharacterDungeonState]:
        result = await self._session.execute(
            select(CharacterDungeonState).where(
                CharacterDungeonState.character_id == character_id
            )
        )
        return list(result.scalars().all())

    async def list_journal(self, character_id: UUID) -> list[JournalEntry]:
        result = await self._session.execute(
            select(JournalEntry)
            .where(JournalEntry.character_id == character_id)
            .order_by(JournalEntry.created_at, JournalEntry.id)
        )
        return list(result.scalars().all())

    async def list_events(self, character_id: UUID) -> list[WorldEvent]:
        result = await self._session.execute(
            select(WorldEvent)
            .where(WorldEvent.character_id == character_id)
            .order_by(WorldEvent.created_at, WorldEvent.id)
        )
        return list(result.scalars().all())

    async def list_memories(self, player_id: UUID, character_id: UUID) -> list[Memory]:
        result = await self._session.execute(
            select(Memory).where(
                Memory.player_id == player_id,
                Memory.source_entity_id == character_id,
                Memory.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def get_active_memory(
        self,
        player_id: UUID,
        memory_type: str,
        entity_type: str,
        entity_id: UUID,
        content_hash: str,
    ) -> Memory | None:
        result = await self._session.execute(
            select(Memory).where(
                Memory.player_id == player_id,
                Memory.memory_type == memory_type,
                Memory.entity_type == entity_type,
                Memory.entity_id == entity_id,
                Memory.content_hash == content_hash,
                Memory.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def active_job(self, character: Character) -> tuple[CharacterJob, Job] | None:
        result = await self._session.execute(
            select(CharacterJob, Job)
            .join(Job, Job.id == CharacterJob.job_id)
            .where(
                CharacterJob.character_id == character.id,
                CharacterJob.job_id == character.active_job_id,
            )
            .with_for_update()
        )
        return result.tuples().one_or_none()

    async def job_skills(self, job_id: UUID) -> list[JobSkill]:
        result = await self._session.execute(
            select(JobSkill).where(JobSkill.job_id == job_id)
        )
        return list(result.scalars().all())

    async def skill_ids(self, character_id: UUID) -> set[UUID]:
        result = await self._session.execute(
            select(CharacterSkill.skill_id).where(
                CharacterSkill.character_id == character_id
            )
        )
        return set(result.scalars().all())

    async def capture(self, player_id: UUID, character_id: UUID) -> WorldSnapshot:
        quest_rows = await self.list_character_quests(player_id, character_id)
        relationships = await self.list_relationships(character_id)
        factions = await self.list_character_factions(character_id)
        dungeons = await self.list_dungeon_states(character_id)
        journal = await self.list_journal(character_id)
        memories = await self.list_memories(player_id, character_id)
        return WorldSnapshot(
            quest_state={
                "quests": [self._quest_payload(row) for _, row in quest_rows if row]
            },
            npc_state={"npc_ids": [str(value.npc_id) for value in relationships]},
            faction_state={
                "factions": [self._faction_payload(value) for value in factions]
            },
            relationships={
                "relationships": [
                    self._relationship_payload(value) for value in relationships
                ]
            },
            journal={"entry_ids": [str(value.id) for value in journal]},
            memories={"memory_ids": [str(value.id) for value in memories]},
            dungeon_state={
                "dungeons": [self._dungeon_payload(value) for value in dungeons]
            },
        )

    async def restore(
        self, player_id: UUID, character_id: UUID, snapshot: WorldSnapshot
    ) -> None:
        await self._restore_quests(player_id, character_id, snapshot.quest_state)
        await self._restore_factions(player_id, character_id, snapshot.faction_state)
        await self._restore_relationships(
            player_id, character_id, snapshot.relationships
        )
        await self._restore_dungeons(player_id, character_id, snapshot.dungeon_state)
        await self._session.flush()

    async def _restore_quests(
        self, player_id: UUID, character_id: UUID, payload: dict[str, JsonValue]
    ) -> None:
        rows = payload.get("quests", [])
        if not isinstance(rows, list):
            raise ValueError("Saved quests must be a list")
        for item in rows:
            if not isinstance(item, dict):
                raise ValueError("Saved quest must be an object")
            quest_id = UUID(str(item["quest_id"]))
            current = await self.get_character_quest(
                character_id, quest_id, for_update=True
            )
            saved_status = str(item["status"])
            if current is not None and current.status in {
                "COMPLETED",
                "FAILED",
                "ARCHIVED",
            }:
                continue
            if current is None:
                current = CharacterQuest(
                    player_id=player_id, character_id=character_id, quest_id=quest_id
                )
                await self.add(current)
            current.status = saved_status
            current.current_step = int(str(item["current_step"]))
            current.step_progress = int(str(item["step_progress"]))
            current.objectives_complete = bool(item["objectives_complete"])
            current.rewards_claimed = bool(item["rewards_claimed"])

    async def _restore_factions(
        self, player_id: UUID, character_id: UUID, payload: dict[str, JsonValue]
    ) -> None:
        rows = payload.get("factions", [])
        if not isinstance(rows, list):
            raise ValueError("Saved factions must be a list")
        for item in rows:
            if not isinstance(item, dict):
                raise ValueError("Saved faction must be an object")
            faction_id = UUID(str(item["faction_id"]))
            row = await self.get_character_faction(
                character_id, faction_id, for_update=True
            )
            if row is None:
                row = CharacterFaction(
                    player_id=player_id,
                    character_id=character_id,
                    faction_id=faction_id,
                )
                await self.add(row)
                row.reputation = int(str(item["reputation"]))
                row.joined = bool(item["joined"])
                row.rank = str(item["rank"])

    async def _restore_relationships(
        self, player_id: UUID, character_id: UUID, payload: dict[str, JsonValue]
    ) -> None:
        rows = payload.get("relationships", [])
        if not isinstance(rows, list):
            raise ValueError("Saved relationships must be a list")
        for item in rows:
            if not isinstance(item, dict):
                raise ValueError("Saved relationship must be an object")
            npc_id = UUID(str(item["npc_id"]))
            row = await self.get_relationship(character_id, npc_id, for_update=True)
            if row is None:
                row = Relationship(
                    player_id=player_id, character_id=character_id, npc_id=npc_id
                )
                await self.add(row)
                for field in (
                    "trust",
                    "friendship",
                    "respect",
                    "fear",
                    "hatred",
                    "loyalty",
                ):
                    setattr(row, field, int(str(item[field])))

    async def _restore_dungeons(
        self, player_id: UUID, character_id: UUID, payload: dict[str, JsonValue]
    ) -> None:
        rows = payload.get("dungeons", [])
        if not isinstance(rows, list):
            raise ValueError("Saved dungeons must be a list")
        for item in rows:
            if not isinstance(item, dict):
                raise ValueError("Saved dungeon must be an object")
            dungeon_id = UUID(str(item["dungeon_id"]))
            row = await self.get_dungeon_state(
                character_id, dungeon_id, for_update=True
            )
            if row is None:
                row = CharacterDungeonState(
                    player_id=player_id,
                    character_id=character_id,
                    dungeon_id=dungeon_id,
                )
                await self.add(row)
            row.entered = row.entered or bool(item["entered"])
            row.cleared = row.cleared or bool(item["cleared"])
            row.boss_alive = row.boss_alive and bool(item["boss_alive"])

    @staticmethod
    def _quest_payload(value: CharacterQuest) -> dict[str, JsonValue]:
        return {
            "quest_id": str(value.quest_id),
            "status": value.status,
            "current_step": value.current_step,
            "step_progress": value.step_progress,
            "objectives_complete": value.objectives_complete,
            "rewards_claimed": value.rewards_claimed,
        }

    @staticmethod
    def _faction_payload(value: CharacterFaction) -> dict[str, JsonValue]:
        return {
            "faction_id": str(value.faction_id),
            "reputation": value.reputation,
            "rank": value.rank,
            "joined": value.joined,
        }

    @staticmethod
    def _relationship_payload(value: Relationship) -> dict[str, JsonValue]:
        return {
            "npc_id": str(value.npc_id),
            "trust": value.trust,
            "friendship": value.friendship,
            "respect": value.respect,
            "fear": value.fear,
            "hatred": value.hatred,
            "loyalty": value.loyalty,
        }

    @staticmethod
    def _dungeon_payload(value: CharacterDungeonState) -> dict[str, JsonValue]:
        return {
            "dungeon_id": str(value.dungeon_id),
            "entered": value.entered,
            "cleared": value.cleared,
            "boss_alive": value.boss_alive,
        }


class WorldUnitOfWork:
    """Own one transaction for all v0.7 canonical state."""

    def __init__(self, session: AsyncSession) -> None:
        self.world = WorldRepository(session)
        self.idempotency = IdempotencyRepository(session)
        self._session = session
        self._transaction: AsyncSessionTransaction | None = None

    async def __aenter__(self) -> "WorldUnitOfWork":
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        return self

    async def lock_key(self, value: str) -> None:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:value, 0))"),
            {"value": value},
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._transaction is None:
            raise RuntimeError("WorldUnitOfWork exited before it was entered")
        await self._transaction.__aexit__(exc_type, exc_value, traceback)


__all__ = [
    "Memory",
    "WorldRepository",
    "WorldSnapshot",
    "WorldUnitOfWork",
]
