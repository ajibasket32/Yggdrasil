from datetime import datetime
from typing import Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue

CURRENT_SAVE_SCHEMA_VERSION = 1
ENGINE_VERSION = "0.8.0"


class SaveSnapshotV1(BaseModel):
    """Complete logical save contract for schema version 1."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    world_tick: int = Field(default=0, ge=0)
    character: dict[str, JsonValue] = Field(default_factory=dict)
    inventory: dict[str, JsonValue] = Field(default_factory=dict)
    equipment: dict[str, JsonValue] = Field(default_factory=dict)
    world_state: dict[str, JsonValue] = Field(default_factory=dict)
    quest_state: dict[str, JsonValue] = Field(default_factory=dict)
    npc_state: dict[str, JsonValue] = Field(default_factory=dict)
    faction_state: dict[str, JsonValue] = Field(default_factory=dict)
    relationships: dict[str, JsonValue] = Field(default_factory=dict)
    journal: dict[str, JsonValue] = Field(default_factory=dict)
    memories: dict[str, JsonValue] = Field(default_factory=dict)
    dungeon_state: dict[str, JsonValue] = Field(default_factory=dict)


class CreateSaveRequest(BaseModel):
    """Public save request; the server owns snapshot assembly."""

    character_id: UUID
    save_name: str | None = Field(default=None, max_length=120)


class LoadSaveRequest(BaseModel):
    """Request to load one owned save."""

    save_id: UUID


class SaveSummary(BaseModel):
    """User-facing metadata for one save slot."""

    save_id: UUID
    character_id: UUID
    save_name: str = Field(min_length=1, max_length=120)
    save_version: int = Field(ge=1)
    world_tick: int = Field(ge=0)
    schema_version: int = Field(ge=1)
    engine_version: str = Field(min_length=1, max_length=32)
    status: str = Field(min_length=1, max_length=20)
    created_at: datetime


class LoadedSave(SaveSummary):
    """Validated snapshot returned by a load operation."""

    snapshot: SaveSnapshotV1


class DeleteSaveResult(BaseModel):
    """Result of recoverable save deletion."""

    save_id: UUID
    deleted: bool


class ResponseMeta(BaseModel):
    """Standard API response metadata."""

    request_id: UUID
    timestamp: datetime
    api_version: Literal["v1"] = "v1"


DataT = TypeVar("DataT")


class ApiResponse[DataT](BaseModel):
    """Standard successful API response envelope."""

    success: Literal[True] = True
    data: DataT
    meta: ResponseMeta
