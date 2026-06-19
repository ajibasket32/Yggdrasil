from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request

from app.api.dependencies import NarrativeServiceDependency
from app.schemas.narrative import (
    DialogueRequest,
    LocationDescriptionRequest,
    LoreRequest,
    NarrativeView,
    QuestFramingRequest,
)
from app.schemas.save import ApiResponse, ResponseMeta

router = APIRouter(tags=["narrative"])
PlayerId = Annotated[UUID, Header(alias="X-Player-ID")]
IdempotencyKey = Annotated[
    str, Header(alias="Idempotency-Key", min_length=1, max_length=200)
]


def _meta(request: Request) -> ResponseMeta:
    return ResponseMeta(
        request_id=UUID(str(request.state.request_id)),
        timestamp=datetime.now(UTC),
    )


@router.post(
    "/npcs/{npc_id}/dialogue",
    response_model=ApiResponse[NarrativeView],
)
async def generate_dialogue(
    npc_id: UUID,
    payload: DialogueRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: NarrativeServiceDependency,
) -> ApiResponse[NarrativeView]:
    """Generate one validated response to a server-approved dialogue topic."""
    return ApiResponse(
        data=await service.dialogue(
            player_id,
            payload.character_id,
            npc_id,
            payload.topic_id,
            idempotency_key,
        ),
        meta=_meta(request),
    )


@router.post("/narrative/lore", response_model=ApiResponse[NarrativeView])
async def generate_lore(
    payload: LoreRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: NarrativeServiceDependency,
) -> ApiResponse[NarrativeView]:
    """Generate optional validated lore for an available canonical entity."""
    return ApiResponse(
        data=await service.lore(
            player_id,
            payload.character_id,
            payload.entity_id,
            payload.entity_type,
            idempotency_key,
        ),
        meta=_meta(request),
    )


@router.post(
    "/quests/{quest_id}/framing",
    response_model=ApiResponse[NarrativeView],
)
async def generate_quest_framing(
    quest_id: UUID,
    payload: QuestFramingRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: NarrativeServiceDependency,
) -> ApiResponse[NarrativeView]:
    """Generate cosmetic framing without changing quest state or rewards."""
    return ApiResponse(
        data=await service.quest_framing(
            player_id,
            payload.character_id,
            quest_id,
            idempotency_key,
        ),
        meta=_meta(request),
    )


@router.post(
    "/locations/{location_id}/description",
    response_model=ApiResponse[NarrativeView],
)
async def generate_location_description(
    location_id: UUID,
    payload: LocationDescriptionRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: NarrativeServiceDependency,
) -> ApiResponse[NarrativeView]:
    """Generate cosmetic atmosphere for the current canonical location."""
    return ApiResponse(
        data=await service.location_description(
            player_id,
            payload.character_id,
            location_id,
            idempotency_key,
        ),
        meta=_meta(request),
    )
