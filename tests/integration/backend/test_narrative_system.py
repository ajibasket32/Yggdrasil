from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.ai.contracts import NarrativeOutput, NarrativeRequest, NarrativeResult
from app.core.database import session_factory
from app.models.gameplay import Character
from app.models.narrative import NarrativeRecord
from app.models.world import CharacterQuest, Relationship
from app.rag.contracts import MemoryContextPackage, RetrievalQuery
from app.rag.errors import QdrantError
from app.repositories.gameplay import GameUnitOfWork
from app.repositories.narrative import NarrativeRepository, NarrativeUnitOfWork
from app.repositories.world import WorldUnitOfWork
from app.schemas.gameplay import CreateCharacterRequest
from app.services.gameplay import CharacterService
from app.services.narrative import NarrativeService
from app.services.narrative_context import NarrativeContextBuilder
from app.services.world import WorldService


class EmptyRetriever:
    async def retrieve(self, query: RetrievalQuery) -> MemoryContextPackage:
        return MemoryContextPackage(
            memories=(),
            estimated_tokens=0,
            truncated=False,
            cache_hit=False,
        )


class UnavailableRetriever:
    async def retrieve(self, query: RetrievalQuery) -> MemoryContextPackage:
        raise QdrantError("vector store unavailable")


class RecordingGenerator:
    def __init__(self, *, fallback: bool = False) -> None:
        self.requests: list[NarrativeRequest] = []
        self.fallback = fallback

    async def generate(self, request: NarrativeRequest) -> NarrativeResult:
        self.requests.append(request)
        return NarrativeResult(
            request_id=request.request_id,
            provider="cached" if self.fallback else "test",
            model="local-fallback" if self.fallback else "test-model",
            output=NarrativeOutput(
                text="The old roots remember who stood watch.",
                tone="wary",
                tags=("grounded",),
                referenced_entity_ids=frozenset(),
            ),
            fallback_used=self.fallback,
            cached=self.fallback,
        )


import typing
async def _prepared_world(player_id: UUID) -> tuple[typing.Any, typing.Any, typing.Any, typing.Any]:
    async with session_factory() as session:
        gameplay = CharacterService(GameUnitOfWork(session))
        definitions = await gameplay.creation_definitions()
        warrior = next(
            value for value in definitions.starting_jobs if value.name == "Warrior"
        )
        character = await gameplay.create_character(
            player_id,
            CreateCharacterRequest(
                name="Narrative Tester",
                race_id=definitions.races[0].id,
                gender="Unspecified",
                alignment="NEUTRAL",
                starting_job_id=warrior.id,
            ),
            f"create-{player_id}",
        )
        greenwood = next(
            value
            for value in await gameplay.locations(player_id, character.id)
            if value.name == "Greenwood Verge"
        )
        await gameplay.travel(
            player_id, character.id, greenwood.id, f"travel-{player_id}"
        )
    async with session_factory() as session:
        world = WorldService(WorldUnitOfWork(session))
        quest = (await world.quests(player_id, character.id))[0]
        await world.accept_quest(
            player_id, character.id, quest.id, f"accept-{player_id}"
        )
        npc = (await world.npcs(player_id, character.id))[0]
        await world.interact(
            player_id, character.id, npc.id, "OFFER_HELP", f"help-{player_id}"
        )
    return character, greenwood, quest, npc


async def _snapshot(character_id: UUID) -> tuple[int, int, str, int]:
    async with session_factory() as session:
        character = await session.get(Character, character_id)
        quest = await session.scalar(
            select(CharacterQuest).where(CharacterQuest.character_id == character_id)
        )
        relationship = await session.scalar(
            select(Relationship).where(Relationship.character_id == character_id)
        )
        assert character is not None
        assert quest is not None
        assert relationship is not None
        return character.current_hp, character.gold, quest.status, relationship.trust


@pytest.mark.asyncio
async def test_dialogue_is_grounded_idempotent_and_read_only(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character, _, quest, npc = await _prepared_world(player_id)
    before = await _snapshot(character.id)
    generator = RecordingGenerator()

    async with session_factory() as session:
        service = NarrativeService(
            NarrativeUnitOfWork(session),
            NarrativeContextBuilder(NarrativeRepository(session), EmptyRetriever()),
            generator,
        )
        first = await service.dialogue(
            player_id, character.id, npc.id, "QUEST", "dialogue-1"
        )
        repeated = await service.dialogue(
            player_id, character.id, npc.id, "QUEST", "dialogue-1"
        )

    assert len(generator.requests) == 1
    instruction = generator.requests[0].instruction
    assert npc.name in instruction
    assert quest.title in instruction
    assert '"trust":5' in instruction
    assert "offered practical aid" in instruction.lower()
    assert first.context_memory_count >= 1
    assert repeated.cached
    assert await _snapshot(character.id) == before

    async with session_factory() as session:
        records = list((await session.scalars(select(NarrativeRecord))).all())
    assert len(records) == 1


@pytest.mark.asyncio
async def test_non_dialogue_context_cache_avoids_duplicate_generation(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character, _, quest, _ = await _prepared_world(player_id)
    generator = RecordingGenerator()

    async with session_factory() as session:
        service = NarrativeService(
            NarrativeUnitOfWork(session),
            NarrativeContextBuilder(NarrativeRepository(session), EmptyRetriever()),
            generator,
        )
        first = await service.quest_framing(
            player_id, character.id, quest.id, "framing-1"
        )
        second = await service.quest_framing(
            player_id, character.id, quest.id, "framing-2"
        )

    assert len(generator.requests) == 1
    assert not first.cached
    assert second.cached


@pytest.mark.asyncio
async def test_qdrant_failure_uses_postgres_memory_and_local_fallback(
    clean_gameplay_database: None,
) -> None:
    player_id = uuid4()
    character, location, _, _ = await _prepared_world(player_id)
    generator = RecordingGenerator(fallback=True)

    async with session_factory() as session:
        service = NarrativeService(
            NarrativeUnitOfWork(session),
            NarrativeContextBuilder(
                NarrativeRepository(session), UnavailableRetriever()
            ),
            generator,
        )
        result = await service.location_description(
            player_id, character.id, location.id, "location-1"
        )

    assert result.fallback_used
    assert result.cached
    assert result.context_memory_count >= 1
    assert "offered practical aid" in generator.requests[0].instruction.lower()
