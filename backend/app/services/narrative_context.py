from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from app.ai.context import (
    NarrativeContext,
    NarrativeMemory,
    NarrativeQuest,
    NarrativeRelationship,
)
from app.models.gameplay import Character
from app.models.memory import Memory
from app.models.world import NPC, CharacterFaction, Faction, Relationship
from app.rag.contracts import MemoryContextPackage, MemoryType, RetrievalQuery
from app.rag.errors import QdrantError
from app.repositories.narrative import NarrativeRepository


class MemoryRetrieverBoundary(Protocol):
    async def retrieve(self, query: RetrievalQuery) -> MemoryContextPackage:
        """Retrieve ranked canonical memory identifiers."""


class NarrativeContextError(ValueError):
    """Canonical narrative context cannot be assembled safely."""


class NarrativeContextBuilder:
    """Assemble bounded, player-scoped context before every AI request."""

    MEMORY_TYPES = (
        MemoryType.NPC,
        MemoryType.FACTION,
        MemoryType.QUEST,
        MemoryType.LOCATION,
        MemoryType.WORLD,
        MemoryType.DIALOGUE,
    )

    def __init__(
        self,
        repository: NarrativeRepository,
        retriever: MemoryRetrieverBoundary,
    ) -> None:
        self._repository = repository
        self._retriever = retriever

    async def for_npc(
        self, player_id: UUID, character_id: UUID, npc_id: UUID, topic_id: str
    ) -> NarrativeContext:
        character = await self._character(player_id, character_id)
        npc = await self._repository.get_npc(npc_id)
        if npc is None or not npc.is_alive:
            raise NarrativeContextError("NPC was not found")
        if npc.home_location_id != character.current_location_id:
            raise NarrativeContextError("NPC is not at the character's location")
        relationship = await self._repository.get_relationship(character.id, npc.id)
        faction, standing = await self._faction(character.id, npc.faction_id)
        return await self._build(
            player_id,
            character,
            topic_id,
            npc=npc,
            faction=faction,
            standing=standing,
            relationship=relationship,
        )

    async def for_entity(
        self,
        player_id: UUID,
        character_id: UUID,
        entity_id: UUID,
        entity_type: str,
        topic_id: str,
    ) -> NarrativeContext:
        character = await self._character(player_id, character_id)
        if entity_type == "quest":
            if await self._repository.get_quest(entity_id) is None:
                raise NarrativeContextError("Quest was not found")
        elif entity_type == "location":
            if entity_id != character.current_location_id:
                raise NarrativeContextError("Only the current location may be described")
        else:
            raise NarrativeContextError("Unsupported narrative entity")
        context = await self._build(player_id, character, topic_id)
        if entity_id not in context.allowed_entity_ids:
            raise NarrativeContextError("Narrative entity is not available to this character")
        return context

    async def _build(
        self,
        player_id: UUID,
        character: Character,
        topic_id: str,
        *,
        npc: NPC | None = None,
        faction: Faction | None = None,
        standing: CharacterFaction | None = None,
        relationship: Relationship | None = None,
    ) -> NarrativeContext:
        location = await self._repository.get_location(character.current_location_id)
        if location is None:
            raise NarrativeContextError("Character location was not found")
        quest_rows = await self._repository.list_quest_context(character.id, location.id)
        quest_context = tuple(
            NarrativeQuest(
                id=row.quest.id,
                title=row.quest.title,
                status=row.state.status if row.state else "NOT_STARTED",
                current_objective=(row.current_step.description if row.current_step else None),
            )
            for row in quest_rows
        )
        query_text = " ".join(
            value
            for value in (
                topic_id,
                npc.name if npc else "",
                faction.name if faction else "",
                location.name,
                *(quest.title for quest in quest_context),
            )
            if value
        )
        memories = await self._memories(player_id, character.id, query_text, relationship, npc)
        recent = (
            await self._repository.recent_dialogue(player_id, character.id, npc.id) if npc else []
        )
        allowed_ids = {
            character.id,
            location.id,
            *(quest.id for quest in quest_context),
            *(memory.entity_id for memory in memories),
        }
        if npc:
            allowed_ids.add(npc.id)
        if faction:
            allowed_ids.add(faction.id)
        return NarrativeContext(
            character_id=character.id,
            character_name=character.name,
            location_id=location.id,
            location_name=location.name,
            npc_id=npc.id if npc else None,
            npc_name=npc.name if npc else None,
            npc_role=npc.role if npc else None,
            npc_personality=npc.personality_profile if npc else {},
            npc_knowledge=npc.knowledge if npc else {},
            faction_id=faction.id if faction else None,
            faction_name=faction.name if faction else None,
            faction_reputation=standing.reputation if standing else 0,
            faction_rank=standing.rank if standing else "OUTSIDER",
            faction_joined=standing.joined if standing else False,
            relationship=self._relationship(relationship),
            quests=quest_context,
            memories=tuple(self._memory(value) for value in memories),
            recent_dialogue=tuple(value.text for value in recent),
            allowed_entity_ids=frozenset(allowed_ids),
        )

    async def _memories(
        self,
        player_id: UUID,
        character_id: UUID,
        query_text: str,
        relationship: Relationship | None,
        npc: NPC | None,
    ) -> list[Memory]:
        weights = {npc.id: self._relationship_weight(relationship)} if npc is not None else {}
        try:
            package = await self._retriever.retrieve(
                RetrievalQuery(
                    player_id=player_id,
                    query_text=query_text,
                    memory_types=self.MEMORY_TYPES,
                    relationship_weights=weights,
                    as_of=datetime.now(UTC),
                    limit=20,
                    max_context_tokens=3000,
                )
            )
            memory_ids = [value.memory_id for value in package.memories]
            ranked = await self._repository.list_context_memories(
                player_id, character_id, memory_ids=memory_ids
            )
            if ranked:
                order = {memory_id: index for index, memory_id in enumerate(memory_ids)}
                ranked.sort(key=lambda value: order[value.id])
                canonical = await self._repository.list_context_memories(
                    player_id, character_id, limit=20
                )
                ranked_ids = {value.id for value in ranked}
                return (ranked + [value for value in canonical if value.id not in ranked_ids])[:20]
        except QdrantError:
            pass
        return await self._repository.list_context_memories(player_id, character_id, limit=20)

    async def _character(self, player_id: UUID, character_id: UUID) -> Character:
        character = await self._repository.get_character(player_id, character_id)
        if character is None:
            raise NarrativeContextError("Character was not found")
        return character

    async def _faction(
        self, character_id: UUID, faction_id: UUID | None
    ) -> tuple[Faction | None, CharacterFaction | None]:
        if faction_id is None:
            return None, None
        return (
            await self._repository.get_faction(faction_id),
            await self._repository.get_faction_standing(character_id, faction_id),
        )

    @staticmethod
    def _relationship(value: Relationship | None) -> NarrativeRelationship:
        return NarrativeRelationship(
            trust=value.trust if value else 0,
            friendship=value.friendship if value else 0,
            respect=value.respect if value else 0,
            fear=value.fear if value else 0,
            hatred=value.hatred if value else 0,
            loyalty=value.loyalty if value else 0,
        )

    @staticmethod
    def _relationship_weight(value: Relationship | None) -> float:
        if value is None:
            return 0
        return (
            max(
                abs(value.trust),
                abs(value.friendship),
                abs(value.respect),
                abs(value.fear),
                abs(value.hatred),
                abs(value.loyalty),
            )
            / 100
        )

    @staticmethod
    def _memory(value: Memory) -> NarrativeMemory:
        return NarrativeMemory(
            id=value.id,
            memory_type=value.memory_type,
            entity_id=value.entity_id,
            summary=value.summary,
            importance=value.importance,
            occurred_at=value.occurred_at,
        )
