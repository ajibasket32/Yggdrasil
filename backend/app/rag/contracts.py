from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemoryType(StrEnum):
    """Canonical memory categories supported by the v0.4 infrastructure."""

    PLAYER = "PLAYER_MEMORY"
    NPC = "NPC_MEMORY"
    FACTION = "FACTION_MEMORY"
    QUEST = "QUEST_MEMORY"
    LOCATION = "LOCATION_MEMORY"
    WORLD = "WORLD_MEMORY"
    DIALOGUE = "DIALOGUE_MEMORY"
    ITEM = "ITEM_MEMORY"
    LORE = "LORE_MEMORY"


class MemoryCreate(BaseModel):
    """Validated canonical memory input from a future engine event."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    memory_type: MemoryType
    source_entity_type: str = Field(min_length=1, max_length=40)
    source_entity_id: UUID
    summary: str = Field(min_length=1, max_length=2000)
    importance: int = Field(ge=1, le=10)
    world_event_id: UUID | None = None
    entity_id: UUID
    entity_type: str = Field(min_length=1, max_length=40)
    participants: frozenset[UUID] = Field(default_factory=frozenset, max_length=50)
    location_id: UUID | None = None
    tags: tuple[str, ...] = Field(default_factory=tuple, max_length=20)
    occurred_at: datetime

    @field_validator(
        "source_entity_type",
        "entity_type",
        mode="before",
    )
    @classmethod
    def normalize_entity_type(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: object) -> object:
        if isinstance(value, str):
            return " ".join(value.split())
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: object) -> object:
        if isinstance(value, list | tuple | set | frozenset):
            return tuple(sorted({str(tag).strip().lower() for tag in value if str(tag).strip()}))
        return value


class MemoryRecord(BaseModel):
    """Provider-neutral view of one canonical memory."""

    model_config = ConfigDict(from_attributes=True, extra="forbid", frozen=True)

    id: UUID
    player_id: UUID
    memory_type: MemoryType
    source_entity_type: str
    source_entity_id: UUID
    summary: str
    importance: int
    world_event_id: UUID | None
    entity_id: UUID
    entity_type: str
    participants: tuple[UUID, ...]
    location_id: UUID | None
    tags: tuple[str, ...]
    occurred_at: datetime
    version: int
    index_status: str


class RetrievalQuery(BaseModel):
    """Player-scoped retrieval request with explicit privacy boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    player_id: UUID
    query_text: str = Field(min_length=1, max_length=2000)
    memory_types: tuple[MemoryType, ...] = Field(min_length=1, max_length=9)
    allowed_entity_ids: frozenset[UUID] = Field(default_factory=frozenset, max_length=100)
    required_tags: frozenset[str] = Field(default_factory=frozenset, max_length=20)
    excluded_tags: frozenset[str] = Field(default_factory=frozenset, max_length=20)
    relationship_weights: dict[UUID, float] = Field(default_factory=dict)
    as_of: datetime
    limit: int = Field(default=20, ge=1, le=20)
    max_context_tokens: int = Field(default=6000, ge=100, le=6000)

    @field_validator("required_tags", "excluded_tags", mode="before")
    @classmethod
    def normalize_filter_tags(cls, value: object) -> object:
        if isinstance(value, list | tuple | set | frozenset):
            return frozenset(str(tag).strip().lower() for tag in value if str(tag).strip())
        return value


class RetrievedMemory(BaseModel):
    """Ranked canonical memory safe to package for any AI provider."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    memory_id: UUID
    memory_type: MemoryType
    entity_id: UUID
    entity_type: str
    summary: str
    importance: int
    occurred_at: datetime
    tags: tuple[str, ...]
    relevance_score: float = Field(ge=0, le=1)
    final_score: float = Field(ge=0, le=1)
    estimated_tokens: int = Field(ge=1)


class MemoryContextPackage(BaseModel):
    """Bounded, provider-neutral context with no game-state mutation fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    memories: tuple[RetrievedMemory, ...]
    estimated_tokens: int = Field(ge=0, le=6000)
    truncated: bool
    cache_hit: bool
