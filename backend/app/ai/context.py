import hashlib
import json
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NarrativeMemory(BaseModel):
    """One canonical memory safe to expose to the narrative layer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    memory_type: str
    entity_id: UUID
    summary: str = Field(max_length=2000)
    importance: int = Field(ge=1, le=10)
    occurred_at: datetime


class NarrativeQuest(BaseModel):
    """Read-only quest context without reward or mutation fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    title: str
    status: str
    current_objective: str | None


class NarrativeRelationship(BaseModel):
    """Read-only engine-owned relationship values."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    trust: int = Field(ge=-100, le=100)
    friendship: int = Field(ge=-100, le=100)
    respect: int = Field(ge=-100, le=100)
    fear: int = Field(ge=-100, le=100)
    hatred: int = Field(ge=-100, le=100)
    loyalty: int = Field(ge=-100, le=100)


class NarrativeContext(BaseModel):
    """Bounded canonical context used for provider-neutral generation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    character_id: UUID
    character_name: str
    location_id: UUID
    location_name: str
    npc_id: UUID | None = None
    npc_name: str | None = None
    npc_role: str | None = None
    npc_personality: dict[str, object] = Field(default_factory=dict)
    npc_knowledge: dict[str, object] = Field(default_factory=dict)
    faction_id: UUID | None = None
    faction_name: str | None = None
    faction_reputation: int = Field(default=0, ge=-1000, le=1000)
    faction_rank: str = "OUTSIDER"
    faction_joined: bool = False
    relationship: NarrativeRelationship | None = None
    quests: tuple[NarrativeQuest, ...] = Field(default_factory=tuple, max_length=10)
    memories: tuple[NarrativeMemory, ...] = Field(default_factory=tuple, max_length=20)
    recent_dialogue: tuple[str, ...] = Field(default_factory=tuple, max_length=10)
    allowed_entity_ids: frozenset[UUID] = Field(default_factory=frozenset, max_length=100)

    def content_hash(self) -> str:
        """Return a stable cache/audit fingerprint for this canonical context."""
        payload = self.model_dump(mode="json")
        payload["allowed_entity_ids"] = sorted(str(value) for value in self.allowed_entity_ids)
        canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
