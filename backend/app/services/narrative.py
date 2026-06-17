import hashlib
import json
from typing import Protocol
from uuid import UUID

from app.ai.context import NarrativeContext
from app.ai.contracts import NarrativeKind, NarrativeRequest, NarrativeResult
from app.ai.prompt_builder import NarrativePromptBuilder
from app.core.metrics import NARRATIVE_GENERATIONS_TOTAL
from app.models.narrative import NarrativeRecord
from app.repositories.narrative import NarrativeUnitOfWork
from app.schemas.narrative import DialogueTopic, NarrativeView
from app.services.narrative_context import (
    NarrativeContextBuilder,
    NarrativeContextError,
)

DIALOGUE_TOPICS: list[DialogueTopic] = [
    "GREETING",
    "QUEST",
    "LOCAL_NEWS",
    "FAREWELL",
]


class NarrativeGenerator(Protocol):
    async def generate(self, request: NarrativeRequest) -> NarrativeResult:
        """Generate validated provider-neutral narrative."""


class NarrativeError(Exception):
    """Stable API boundary for cosmetic narrative failures."""

    code = "NARRATIVE_ERROR"
    status_code = 400


class NarrativeNotFoundError(NarrativeError):
    code = "NARRATIVE_CONTEXT_NOT_FOUND"
    status_code = 404


class NarrativeIdempotencyConflict(NarrativeError):
    code = "IDEMPOTENCY_KEY_REUSED"
    status_code = 409


class NarrativeService:
    """Generate, cache, and store validated cosmetic narrative only."""

    def __init__(
        self,
        unit_of_work: NarrativeUnitOfWork,
        context_builder: NarrativeContextBuilder,
        generator: NarrativeGenerator,
        prompt_builder: NarrativePromptBuilder | None = None,
    ) -> None:
        self._uow = unit_of_work
        self._contexts = context_builder
        self._generator = generator
        self._prompts = prompt_builder or NarrativePromptBuilder()

    async def dialogue(
        self,
        player_id: UUID,
        character_id: UUID,
        npc_id: UUID,
        topic_id: DialogueTopic,
        request_key: str,
    ) -> NarrativeView:
        return await self._generate(
            player_id=player_id,
            character_id=character_id,
            entity_id=npc_id,
            entity_type="npc",
            kind=NarrativeKind.DIALOGUE,
            topic_id=topic_id,
            request_key=request_key,
            npc_id=npc_id,
        )

    async def lore(
        self,
        player_id: UUID,
        character_id: UUID,
        entity_id: UUID,
        entity_type: str,
        request_key: str,
    ) -> NarrativeView:
        return await self._generate(
            player_id=player_id,
            character_id=character_id,
            entity_id=entity_id,
            entity_type=entity_type,
            kind=NarrativeKind.LORE,
            topic_id="LORE",
            request_key=request_key,
        )

    async def quest_framing(
        self,
        player_id: UUID,
        character_id: UUID,
        quest_id: UUID,
        request_key: str,
    ) -> NarrativeView:
        return await self._generate(
            player_id=player_id,
            character_id=character_id,
            entity_id=quest_id,
            entity_type="quest",
            kind=NarrativeKind.NARRATION,
            topic_id="QUEST_FRAMING",
            request_key=request_key,
        )

    async def location_description(
        self,
        player_id: UUID,
        character_id: UUID,
        location_id: UUID,
        request_key: str,
    ) -> NarrativeView:
        return await self._generate(
            player_id=player_id,
            character_id=character_id,
            entity_id=location_id,
            entity_type="location",
            kind=NarrativeKind.DESCRIPTION,
            topic_id="LOCATION_DESCRIPTION",
            request_key=request_key,
        )

    async def _generate(
        self,
        *,
        player_id: UUID,
        character_id: UUID,
        entity_id: UUID,
        entity_type: str,
        kind: NarrativeKind,
        topic_id: str,
        request_key: str,
        npc_id: UUID | None = None,
    ) -> NarrativeView:
        fingerprint = self._fingerprint(
            character_id, entity_id, entity_type, kind, topic_id
        )
        async with self._uow:
            prior = await self._uow.narrative.get_by_request(
                player_id, kind.value, request_key
            )
            if prior is not None:
                if prior.request_fingerprint != fingerprint:
                    raise NarrativeIdempotencyConflict(
                        "Idempotency key was already used with a different request"
                    )
                return self._view(prior, cached=True)
            try:
                context = (
                    await self._contexts.for_npc(
                        player_id, character_id, npc_id, topic_id
                    )
                    if npc_id
                    else await self._contexts.for_entity(
                        player_id,
                        character_id,
                        entity_id,
                        entity_type,
                        topic_id,
                    )
                )
            except NarrativeContextError as error:
                raise NarrativeNotFoundError(str(error)) from error
            instruction, prompt_version = self._prompts.build(kind, context, topic_id)
            context_hash = context.content_hash()
            cached = (
                await self._uow.narrative.find_cached(
                    player_id,
                    character_id,
                    kind.value,
                    entity_id,
                    topic_id,
                    prompt_version,
                    context_hash,
                )
                if kind != NarrativeKind.DIALOGUE
                else None
            )
        if cached is not None:
            record = self._cached_copy(
                cached, request_key, fingerprint, context, npc_id
            )
            async with self._uow:
                await self._uow.narrative.add(record)
            NARRATIVE_GENERATIONS_TOTAL.labels(kind.value, "cache").inc()
            return self._view(record, cached=True, context=context)

        result = await self._generator.generate(
            NarrativeRequest(
                actor_id=player_id,
                kind=kind,
                instruction=instruction,
                allowed_entity_ids=context.allowed_entity_ids,
                max_output_tokens=500,
            )
        )
        record = self._record(
            result,
            kind,
            player_id,
            character_id,
            entity_id,
            entity_type,
            topic_id,
            prompt_version,
            context_hash,
            request_key,
            fingerprint,
            npc_id,
        )
        async with self._uow:
            await self._uow.narrative.add(record)
        NARRATIVE_GENERATIONS_TOTAL.labels(
            kind.value, "fallback" if result.fallback_used else "provider"
        ).inc()
        return self._view(record, context=context)

    @staticmethod
    def _record(
        result: NarrativeResult,
        kind: NarrativeKind,
        player_id: UUID,
        character_id: UUID,
        entity_id: UUID,
        entity_type: str,
        topic_id: str,
        prompt_version: str,
        context_hash: str,
        request_key: str,
        fingerprint: str,
        npc_id: UUID | None,
    ) -> NarrativeRecord:
        return NarrativeRecord(
            player_id=player_id,
            character_id=character_id,
            npc_id=npc_id,
            entity_id=entity_id,
            entity_type=entity_type,
            kind=kind.value,
            topic_id=topic_id,
            request_key=request_key,
            request_fingerprint=fingerprint,
            prompt_version=prompt_version,
            context_hash=context_hash,
            provider=result.provider,
            model=result.model,
            text=result.output.text,
            tone=result.output.tone,
            tags=list(result.output.tags),
            referenced_entity_ids=[
                str(value)
                for value in sorted(result.output.referenced_entity_ids, key=str)
            ],
            fallback_used=result.fallback_used,
            cached=result.cached,
        )

    @staticmethod
    def _cached_copy(
        source: NarrativeRecord,
        request_key: str,
        fingerprint: str,
        context: NarrativeContext,
        npc_id: UUID | None,
    ) -> NarrativeRecord:
        return NarrativeRecord(
            player_id=source.player_id,
            character_id=source.character_id,
            npc_id=npc_id,
            entity_id=source.entity_id,
            entity_type=source.entity_type,
            kind=source.kind,
            topic_id=source.topic_id,
            request_key=request_key,
            request_fingerprint=fingerprint,
            prompt_version=source.prompt_version,
            context_hash=context.content_hash(),
            provider=source.provider,
            model=source.model,
            text=source.text,
            tone=source.tone,
            tags=list(source.tags),
            referenced_entity_ids=list(source.referenced_entity_ids),
            fallback_used=source.fallback_used,
            cached=True,
        )

    @staticmethod
    def _view(
        record: NarrativeRecord,
        *,
        cached: bool | None = None,
        context: NarrativeContext | None = None,
    ) -> NarrativeView:
        return NarrativeView(
            speaker_name=context.npc_name if context else None,
            text=record.text,
            tone=record.tone,
            tags=list(record.tags),
            fallback_used=record.fallback_used,
            cached=record.cached if cached is None else cached,
            prompt_version=record.prompt_version,
            context_memory_count=len(context.memories) if context else 0,
            available_topics=DIALOGUE_TOPICS if record.kind == "dialogue" else [],
        )

    @staticmethod
    def _fingerprint(
        character_id: UUID,
        entity_id: UUID,
        entity_type: str,
        kind: NarrativeKind,
        topic_id: str,
    ) -> str:
        payload = json.dumps(
            {
                "character_id": str(character_id),
                "entity_id": str(entity_id),
                "entity_type": entity_type,
                "kind": kind.value,
                "topic_id": topic_id,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
