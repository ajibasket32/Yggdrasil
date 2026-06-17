from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request

from app.api.dependencies import WorldServiceDependency
from app.schemas.save import ApiResponse, ResponseMeta
from app.schemas.world import (
    DungeonMutationRequest,
    DungeonView,
    FactionMutationRequest,
    FactionView,
    JournalEntryView,
    NPCInteractionRequest,
    NPCInteractionResult,
    NPCView,
    QuestMutationRequest,
    QuestView,
    RelationshipView,
    WorldStateView,
)

router = APIRouter(tags=["world"])
PlayerId = Annotated[UUID, Header(alias="X-Player-ID")]
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=200)]


def _meta(request: Request) -> ResponseMeta:
    return ResponseMeta(
        request_id=UUID(str(request.state.request_id)),
        timestamp=datetime.now(UTC),
    )


@router.get(
    "/characters/{character_id}/quests",
    response_model=ApiResponse[list[QuestView]],
)
async def list_quests(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: WorldServiceDependency,
) -> ApiResponse[list[QuestView]]:
    """List location-available and known character quests."""
    return ApiResponse(data=await service.quests(player_id, character_id), meta=_meta(request))


@router.post("/quests/{quest_id}/accept", response_model=ApiResponse[QuestView])
async def accept_quest(
    quest_id: UUID,
    payload: QuestMutationRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: WorldServiceDependency,
) -> ApiResponse[QuestView]:
    """Accept an available quest through the Quest Engine."""
    return ApiResponse(
        data=await service.accept_quest(player_id, payload.character_id, quest_id, idempotency_key),
        meta=_meta(request),
    )


@router.post("/quests/{quest_id}/submit", response_model=ApiResponse[QuestView])
async def submit_quest(
    quest_id: UUID,
    payload: QuestMutationRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: WorldServiceDependency,
) -> ApiResponse[QuestView]:
    """Complete objectives and apply engine-owned rewards atomically."""
    return ApiResponse(
        data=await service.submit_quest(player_id, payload.character_id, quest_id, idempotency_key),
        meta=_meta(request),
    )


@router.post("/quests/{quest_id}/fail", response_model=ApiResponse[QuestView])
async def fail_quest(
    quest_id: UUID,
    payload: QuestMutationRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: WorldServiceDependency,
) -> ApiResponse[QuestView]:
    """Fail an active quest through the Quest Engine."""
    return ApiResponse(
        data=await service.fail_quest(player_id, payload.character_id, quest_id, idempotency_key),
        meta=_meta(request),
    )


@router.post("/quests/{quest_id}/archive", response_model=ApiResponse[QuestView])
async def archive_quest(
    quest_id: UUID,
    payload: QuestMutationRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: WorldServiceDependency,
) -> ApiResponse[QuestView]:
    """Archive a terminal quest through the Quest Engine."""
    return ApiResponse(
        data=await service.archive_quest(
            player_id, payload.character_id, quest_id, idempotency_key
        ),
        meta=_meta(request),
    )


@router.get(
    "/characters/{character_id}/npcs",
    response_model=ApiResponse[list[NPCView]],
)
async def list_npcs(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: WorldServiceDependency,
) -> ApiResponse[list[NPCView]]:
    """List deterministic NPCs at the character's location."""
    return ApiResponse(data=await service.npcs(player_id, character_id), meta=_meta(request))


@router.post(
    "/npcs/{npc_id}/interact",
    response_model=ApiResponse[NPCInteractionResult],
)
async def interact_with_npc(
    npc_id: UUID,
    payload: NPCInteractionRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: WorldServiceDependency,
) -> ApiResponse[NPCInteractionResult]:
    """Resolve one server-issued NPC menu action without AI."""
    return ApiResponse(
        data=await service.interact(
            player_id,
            payload.character_id,
            npc_id,
            payload.action_id,
            idempotency_key,
        ),
        meta=_meta(request),
    )


@router.get(
    "/npcs/{npc_id}/relationship",
    response_model=ApiResponse[RelationshipView],
)
async def get_relationship(
    npc_id: UUID,
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: WorldServiceDependency,
) -> ApiResponse[RelationshipView]:
    """Return engine-owned relationship dimensions."""
    return ApiResponse(
        data=await service.relationship(player_id, character_id, npc_id),
        meta=_meta(request),
    )


@router.get(
    "/characters/{character_id}/factions",
    response_model=ApiResponse[list[FactionView]],
)
async def list_factions(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: WorldServiceDependency,
) -> ApiResponse[list[FactionView]]:
    """List faction definitions and character standing."""
    return ApiResponse(data=await service.factions(player_id, character_id), meta=_meta(request))


@router.post("/factions/{faction_id}/join", response_model=ApiResponse[FactionView])
async def join_faction(
    faction_id: UUID,
    payload: FactionMutationRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: WorldServiceDependency,
) -> ApiResponse[FactionView]:
    """Persist permanent faction membership."""
    return ApiResponse(
        data=await service.join_faction(
            player_id, payload.character_id, faction_id, idempotency_key
        ),
        meta=_meta(request),
    )


@router.get(
    "/characters/{character_id}/dungeons",
    response_model=ApiResponse[list[DungeonView]],
)
async def list_dungeons(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: WorldServiceDependency,
) -> ApiResponse[list[DungeonView]]:
    """List visible and previously entered dungeons."""
    return ApiResponse(data=await service.dungeons(player_id, character_id), meta=_meta(request))


@router.post("/dungeons/{dungeon_id}/enter", response_model=ApiResponse[DungeonView])
async def enter_dungeon(
    dungeon_id: UUID,
    payload: DungeonMutationRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: WorldServiceDependency,
) -> ApiResponse[DungeonView]:
    """Persist dungeon entry."""
    return ApiResponse(
        data=await service.enter_dungeon(
            player_id, payload.character_id, dungeon_id, idempotency_key
        ),
        meta=_meta(request),
    )


@router.post("/dungeons/{dungeon_id}/clear", response_model=ApiResponse[DungeonView])
async def clear_dungeon(
    dungeon_id: UUID,
    payload: DungeonMutationRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: WorldServiceDependency,
) -> ApiResponse[DungeonView]:
    """Permanently clear one dungeon and its boss."""
    return ApiResponse(
        data=await service.clear_dungeon(
            player_id, payload.character_id, dungeon_id, idempotency_key
        ),
        meta=_meta(request),
    )


@router.get(
    "/characters/{character_id}/journal",
    response_model=ApiResponse[list[JournalEntryView]],
)
async def list_journal(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: WorldServiceDependency,
) -> ApiResponse[list[JournalEntryView]]:
    """Return permanent engine-authored journal entries."""
    return ApiResponse(data=await service.journal(player_id, character_id), meta=_meta(request))


@router.get(
    "/characters/{character_id}/world",
    response_model=ApiResponse[WorldStateView],
)
async def get_world_state(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: WorldServiceDependency,
) -> ApiResponse[WorldStateView]:
    """Return the bounded canonical v0.7 world state."""
    return ApiResponse(data=await service.state(player_id, character_id), meta=_meta(request))
