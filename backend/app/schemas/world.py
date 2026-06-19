from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    minimum_level: int = Field(ge=1)
    status: QuestStatusValue
    objectives_complete: bool
    rewards_claimed: bool
    current_step: int = Field(ge=0)
    steps: list[QuestStepView]
    rewards: dict[str, int]


class QuestMutationRequest(BaseModel):
    character_id: UUID


class NPCView(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=100)
    occupation: str = Field(min_length=1, max_length=100)
    role: str = Field(min_length=1, max_length=50)
    faction_id: UUID | None
    current_location_id: UUID
    personality_profile: dict[str, object]
    knowledge: dict[str, object]
    is_alive: bool
    available_actions: list[str]
    shop_id: UUID | None = None


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
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    reputation: int = Field(ge=-1000000, le=1000000)
    rank: str = Field(min_length=1, max_length=50)
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


class ShopItemView(BaseModel):
    item_id: UUID
    name: str
    description: str
    price: int
    rarity: str
    item_type: str


class ShopView(BaseModel):
    id: UUID
    name: str
    description: str
    owner_npc_id: UUID
    items: list[ShopItemView]


class ShopPurchaseRequest(BaseModel):
    character_id: UUID
    shop_id: UUID
    item_id: UUID


class ShopPurchaseResult(BaseModel):
    character_id: UUID
    item_id: UUID
    price_paid: int
    gold_remaining: int


class InnRestRequest(BaseModel):
    character_id: UUID
    npc_id: UUID


class InnRestResult(BaseModel):
    character_id: UUID
    hp_restored: int
    mp_restored: int
    price_paid: int
    gold_remaining: int
    current_hp: int
    current_mp: int


class WorldStateView(BaseModel):
    world_tick: int
    npcs: list[NPCView]
    factions: list[FactionView]
    dungeons: list[DungeonView]
    active_world_events: list[WorldEventView]
