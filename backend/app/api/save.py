from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request

from app.api.dependencies import SaveServiceDependency
from app.schemas.save import (
    ApiResponse,
    CreateSaveRequest,
    DeleteSaveResult,
    LoadedSave,
    LoadSaveRequest,
    ResponseMeta,
    SaveSummary,
)

router = APIRouter(tags=["save"])

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


@router.post(
    "/save",
    response_model=ApiResponse[SaveSummary],
    status_code=201,
)
async def create_save(
    payload: CreateSaveRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: SaveServiceDependency,
) -> ApiResponse[SaveSummary]:
    """Create one complete server-owned snapshot atomically."""
    result = await service.create_save(
        player_id,
        payload.character_id,
        payload.save_name,
        idempotency_key,
    )
    return ApiResponse(data=result, meta=_meta(request))


@router.get("/saves", response_model=ApiResponse[list[SaveSummary]])
async def list_saves(
    request: Request,
    player_id: PlayerId,
    service: SaveServiceDependency,
) -> ApiResponse[list[SaveSummary]]:
    """List active saves owned by the current player."""
    result = await service.list_saves(player_id)
    return ApiResponse(data=result, meta=_meta(request))


@router.post("/load", response_model=ApiResponse[LoadedSave])
async def load_save(
    payload: LoadSaveRequest,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: SaveServiceDependency,
) -> ApiResponse[LoadedSave]:
    """Validate, migrate if needed, and load one coherent snapshot."""
    result = await service.load_save(
        player_id,
        payload.save_id,
        idempotency_key,
    )
    return ApiResponse(data=result, meta=_meta(request))


@router.delete("/save/{save_id}", response_model=ApiResponse[DeleteSaveResult])
async def delete_save(
    save_id: UUID,
    request: Request,
    player_id: PlayerId,
    idempotency_key: IdempotencyKey,
    service: SaveServiceDependency,
) -> ApiResponse[DeleteSaveResult]:
    """Soft-delete an owned save while preserving required recovery points."""
    result = await service.delete_save(player_id, save_id, idempotency_key)
    return ApiResponse(data=result, meta=_meta(request))
