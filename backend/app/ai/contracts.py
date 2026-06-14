from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class NarrativeKind(StrEnum):
    """Permitted synthetic narrative categories for the provider layer."""

    DIALOGUE = "dialogue"
    LORE = "lore"
    NARRATION = "narration"
    DESCRIPTION = "description"


class NarrativeRequest(BaseModel):
    """Provider-neutral request containing no writable gameplay state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: UUID = Field(default_factory=uuid4)
    actor_id: UUID
    kind: NarrativeKind
    instruction: str = Field(min_length=1, max_length=4000)
    allowed_entity_ids: frozenset[UUID] = Field(default_factory=frozenset)
    max_output_tokens: int = Field(default=500, ge=1, le=1000)


class NarrativeOutput(BaseModel):
    """Validated narrative data; deliberately unable to encode game mutations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str = Field(min_length=1, max_length=6000)
    tone: str = Field(min_length=1, max_length=40)
    tags: tuple[str, ...] = Field(default_factory=tuple, max_length=8)
    referenced_entity_ids: frozenset[UUID] = Field(default_factory=frozenset)


class ProviderGeneration(BaseModel):
    """Raw provider result before narrative validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    model: str
    content: str
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)


class NarrativeResult(BaseModel):
    """Validated orchestrator result returned to future narrative services."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: UUID
    provider: str
    model: str
    output: NarrativeOutput
    fallback_used: bool
    cached: bool


class ProviderAdapter(Protocol):
    """Provider-neutral adapter contract."""

    name: str

    async def generate(self, request: NarrativeRequest) -> ProviderGeneration:
        """Generate one raw structured narrative response."""


class RequestBudget(Protocol):
    """Request-rate budget boundary used by the orchestrator."""

    async def allow(self, actor_id: UUID) -> bool:
        """Return whether the actor may consume another provider request."""
