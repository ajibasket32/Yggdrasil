from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

QuestStatusValue = Literal["NOT_STARTED", "ACTIVE", "COMPLETED", "FAILED", "ARCHIVED"]


class QuestStepView(BaseModel):
    id: UUID
    sequence: int
    objective_type: str
    target_id: UUID
    description: str
    required_count: int
    progress: int
    complete: bool


class QuestView(BaseModel):
    id: UUID
    title: str
    description: str
    minimum_level: int
    status: QuestStatusValue
    objectives_complete: bool
    rewards_claimed: bool
    current_step: int
    steps: list[QuestStepView]
    rewards: dict[str, int]


class QuestMutationRequest(BaseModel):
    character_id: UUID


class NPCView(BaseModel):
    id: UUID
    name: str
    occupation: str
    role: str
    faction_id: UUID | None
    current_location_id: UUID
    personality_profile: dict[str, object]
    knowledge: dict[str, object]
    is_alive: bool
    available_actions: list[str]


class NPCInteractionRequest(BaseModel):
    character_id: UUID
    action_id: Literal["GREET", "OFFER_HELP"]


class RelationshipView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    npc_id: UUID
    character_id: UUID
    trust: int
    friendship: int
    respect: int
    fear: int
    hatred: int
    loyalty: int


class NPCInteractionResult(BaseModel):
    npc: NPCView
    relationship: RelationshipView
    action_id: str
    result_text: str
    quest_progressed: bool


class FactionView(BaseModel):
    id: UUID
    name: str
    description: str
    reputation: int
    rank: str
    joined: bool


class FactionMutationRequest(BaseModel):
    character_id: UUID


class DungeonView(BaseModel):
    id: UUID
    name: str
    description: str
    location_id: UUID
    recommended_level: int
    entered: bool
    cleared: bool
    boss_alive: bool


class DungeonMutationRequest(BaseModel):
    character_id: UUID


class JournalEntryView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    title: str
    body: str
    quest_id: UUID | None
    created_at: datetime


class WorldEventView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    location_id: UUID | None
    faction_id: UUID | None
    quest_id: UUID | None
    payload: dict[str, object]
    created_at: datetime


class WorldStateView(BaseModel):
    world_tick: int
    npcs: list[NPCView]
    factions: list[FactionView]
    dungeons: list[DungeonView]
    active_world_events: list[WorldEventView]
