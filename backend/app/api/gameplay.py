from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request

from app.api.dependencies import CharacterServiceDependency
from app.schemas.gameplay import (
    AwardExperienceRequest,
    CharacterCreationDefinitions,
    CharacterSheet,
    CharacterSummary,
    CreateCharacterRequest,
    DropItemRequest,
    EquipItemRequest,
    EquipmentView,
    InventoryView,
    JobMutationRequest,
    JobProgressView,
    LocationView,
    MergeStackRequest,
    SkillView,
    SortInventoryRequest,
    SplitStackRequest,
    TravelRequest,
    TravelResult,
    UnequipItemRequest,
)
from app.schemas.save import ApiResponse, ResponseMeta

router = APIRouter(tags=["gameplay"])

PlayerId = Annotated[UUID, Header(alias="X-Player-ID")]
IdempotencyKey = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=1, max_length=200),
]


def _meta(request: Request) -> ResponseMeta:
    return ResponseMeta(
        request_id=UUID(str(request.state.request_id)),
        timestamp=datetime.now(UTC),
    )


@router.get(
    "/character-definitions",
    response_model=ApiResponse[CharacterCreationDefinitions],
)
async def character_definitions(
    request: Request,
    service: CharacterServiceDependency,
) -> ApiResponse[CharacterCreationDefinitions]:
    """Return engine-owned character creation definitions."""
    return ApiResponse(data=await service.creation_definitions(), meta=_meta(request))


@router.post(
    "/characters",
    response_model=ApiResponse[CharacterSheet],
    status_code=201,
)
async def create_character(
    payload: CreateCharacterRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[CharacterSheet]:
    """Create one complete canonical character atomically."""
    result = await service.create_character(player_id, payload, idempotency_key)
    return ApiResponse(data=result, meta=_meta(request))


@router.get("/characters", response_model=ApiResponse[list[CharacterSummary]])
async def list_characters(
    request: Request,
    player_id: PlayerId,
    service: CharacterServiceDependency,
) -> ApiResponse[list[CharacterSummary]]:
    """List characters owned by the current player."""
    return ApiResponse(
        data=await service.list_characters(player_id), meta=_meta(request)
    )


@router.get(
    "/characters/{character_id}",
    response_model=ApiResponse[CharacterSheet],
)
async def get_character(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: CharacterServiceDependency,
) -> ApiResponse[CharacterSheet]:
    """Return the authoritative character sheet."""
    return ApiResponse(
        data=await service.get_character(player_id, character_id),
        meta=_meta(request),
    )


@router.get(
    "/characters/{character_id}/jobs",
    response_model=ApiResponse[list[JobProgressView]],
)
async def get_character_jobs(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: CharacterServiceDependency,
) -> ApiResponse[list[JobProgressView]]:
    """List every unlocked job and its deterministic progress."""
    sheet = await service.get_character(player_id, character_id)
    return ApiResponse(data=sheet.jobs, meta=_meta(request))


@router.get(
    "/characters/{character_id}/skills",
    response_model=ApiResponse[list[SkillView]],
)
async def get_character_skills(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: CharacterServiceDependency,
) -> ApiResponse[list[SkillView]]:
    """List every skill unlocked by engine-owned progression."""
    sheet = await service.get_character(player_id, character_id)
    return ApiResponse(data=sheet.skills, meta=_meta(request))


@router.post(
    "/characters/{character_id}/progression/experience",
    response_model=ApiResponse[CharacterSheet],
)
async def award_experience(
    character_id: UUID,
    payload: AwardExperienceRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[CharacterSheet]:
    """Apply an engine-authorized deterministic XP event."""
    return ApiResponse(
        data=await service.award_experience(
            player_id, character_id, payload.amount, idempotency_key
        ),
        meta=_meta(request),
    )


@router.post(
    "/characters/{character_id}/jobs/unlock",
    response_model=ApiResponse[CharacterSheet],
)
async def unlock_job(
    character_id: UUID,
    payload: JobMutationRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[CharacterSheet]:
    """Unlock a job only when its data-driven prerequisites pass."""
    return ApiResponse(
        data=await service.unlock_job(
            player_id, character_id, payload.job_id, idempotency_key
        ),
        meta=_meta(request),
    )


@router.post(
    "/characters/{character_id}/jobs/change",
    response_model=ApiResponse[CharacterSheet],
)
async def change_job(
    character_id: UUID,
    payload: JobMutationRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[CharacterSheet]:
    """Change the active job to one already unlocked."""
    return ApiResponse(
        data=await service.change_job(
            player_id, character_id, payload.job_id, idempotency_key
        ),
        meta=_meta(request),
    )


@router.get(
    "/characters/{character_id}/inventory",
    response_model=ApiResponse[InventoryView],
)
async def get_inventory(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: CharacterServiceDependency,
) -> ApiResponse[InventoryView]:
    """Return the authoritative inventory."""
    return ApiResponse(
        data=await service.inventory(player_id, character_id),
        meta=_meta(request),
    )


@router.post("/inventory/drop", response_model=ApiResponse[InventoryView])
async def drop_item(
    payload: DropItemRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[InventoryView]:
    """Drop a droppable item; protected quest items fail closed."""
    return ApiResponse(
        data=await service.drop_item(
            player_id,
            payload.character_id,
            payload.inventory_item_id,
            payload.quantity,
            idempotency_key,
        ),
        meta=_meta(request),
    )


@router.post(
    "/inventory/split-stack",
    response_model=ApiResponse[InventoryView],
)
async def split_stack(
    payload: SplitStackRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[InventoryView]:
    """Split one stack into a free inventory slot."""
    return ApiResponse(
        data=await service.split_stack(
            player_id,
            payload.character_id,
            payload.inventory_item_id,
            payload.quantity,
            idempotency_key,
        ),
        meta=_meta(request),
    )


@router.post(
    "/inventory/merge-stack",
    response_model=ApiResponse[InventoryView],
)
async def merge_stack(
    payload: MergeStackRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[InventoryView]:
    """Merge compatible stacks up to their engine-defined maximum."""
    return ApiResponse(
        data=await service.merge_stacks(
            player_id,
            payload.character_id,
            payload.source_inventory_item_id,
            payload.target_inventory_item_id,
            idempotency_key,
        ),
        meta=_meta(request),
    )


@router.post("/inventory/sort", response_model=ApiResponse[InventoryView])
async def sort_inventory(
    payload: SortInventoryRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[InventoryView]:
    """Apply deterministic server-side inventory ordering."""
    return ApiResponse(
        data=await service.sort_inventory(
            player_id, payload.character_id, idempotency_key
        ),
        meta=_meta(request),
    )


@router.get(
    "/characters/{character_id}/equipment",
    response_model=ApiResponse[EquipmentView],
)
async def get_equipment(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: CharacterServiceDependency,
) -> ApiResponse[EquipmentView]:
    """Return all equipment slots and deterministic stat bonuses."""
    return ApiResponse(
        data=await service.equipment(player_id, character_id),
        meta=_meta(request),
    )


@router.post("/equipment/equip", response_model=ApiResponse[EquipmentView])
async def equip_item(
    payload: EquipItemRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[EquipmentView]:
    """Equip one compatible unique inventory item."""
    return ApiResponse(
        data=await service.equip(
            player_id,
            payload.character_id,
            payload.inventory_item_id,
            payload.slot_id,
            idempotency_key,
        ),
        meta=_meta(request),
    )


@router.post("/equipment/unequip", response_model=ApiResponse[EquipmentView])
async def unequip_item(
    payload: UnequipItemRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[EquipmentView]:
    """Clear one equipment slot without deleting its inventory item."""
    return ApiResponse(
        data=await service.unequip(
            player_id, payload.character_id, payload.slot_id, idempotency_key
        ),
        meta=_meta(request),
    )


@router.get(
    "/characters/{character_id}/locations",
    response_model=ApiResponse[list[LocationView]],
)
async def get_locations(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: CharacterServiceDependency,
) -> ApiResponse[list[LocationView]]:
    """Return permanent discoveries and currently reachable locations."""
    return ApiResponse(
        data=await service.locations(player_id, character_id),
        meta=_meta(request),
    )


@router.post(
    "/characters/{character_id}/travel",
    response_model=ApiResponse[TravelResult],
)
async def travel(
    character_id: UUID,
    payload: TravelRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CharacterServiceDependency,
) -> ApiResponse[TravelResult]:
    """Move only across a valid canonical route and persist discovery."""
    return ApiResponse(
        data=await service.travel(
            player_id, character_id, payload.destination_id, idempotency_key
        ),
        meta=_meta(request),
    )
