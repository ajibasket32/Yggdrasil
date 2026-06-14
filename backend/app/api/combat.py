from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request

from app.api.dependencies import CombatServiceDependency
from app.schemas.combat import (
    CombatActionRequest,
    CombatLogView,
    CombatStateView,
    EncounterDefinitionView,
    FleeCombatRequest,
    StartCombatRequest,
)
from app.schemas.save import ApiResponse, ResponseMeta

router = APIRouter(tags=["combat"])

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
    "/characters/{character_id}/encounters",
    response_model=ApiResponse[list[EncounterDefinitionView]],
)
async def available_encounters(
    character_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: CombatServiceDependency,
) -> ApiResponse[list[EncounterDefinitionView]]:
    """List enabled encounters at the character's canonical location."""
    return ApiResponse(
        data=await service.available_encounters(player_id, character_id),
        meta=_meta(request),
    )


@router.post(
    "/combat/start",
    response_model=ApiResponse[CombatStateView],
    status_code=201,
)
async def start_combat(
    payload: StartCombatRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CombatServiceDependency,
) -> ApiResponse[CombatStateView]:
    """Create a seeded canonical encounter atomically."""
    return ApiResponse(
        data=await service.start(player_id, payload, idempotency_key),
        meta=_meta(request),
    )


@router.post("/combat/action", response_model=ApiResponse[CombatStateView])
async def combat_action(
    payload: CombatActionRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CombatServiceDependency,
) -> ApiResponse[CombatStateView]:
    """Resolve one player turn and deterministic enemy responses."""
    return ApiResponse(
        data=await service.act(player_id, payload, idempotency_key),
        meta=_meta(request),
    )


@router.post("/combat/flee", response_model=ApiResponse[CombatStateView])
async def flee_combat(
    payload: FleeCombatRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: CombatServiceDependency,
) -> ApiResponse[CombatStateView]:
    """Attempt seeded escape and persist the outcome."""
    return ApiResponse(
        data=await service.flee(player_id, payload.combat_id, idempotency_key),
        meta=_meta(request),
    )


@router.get("/combat/{combat_id}", response_model=ApiResponse[CombatStateView])
async def get_combat(
    combat_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: CombatServiceDependency,
) -> ApiResponse[CombatStateView]:
    """Return canonical combat state."""
    return ApiResponse(
        data=await service.get(player_id, combat_id),
        meta=_meta(request),
    )


@router.get(
    "/combat/{combat_id}/log",
    response_model=ApiResponse[list[CombatLogView]],
)
async def get_combat_log(
    combat_id: UUID,
    request: Request,
    player_id: PlayerId,
    service: CombatServiceDependency,
) -> ApiResponse[list[CombatLogView]]:
    """Return the complete ordered combat log."""
    return ApiResponse(
        data=await service.logs(player_id, combat_id),
        meta=_meta(request),
    )
