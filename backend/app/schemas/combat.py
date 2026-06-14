from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EncounterDefinitionView(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=100)
    monster_name: str = Field(min_length=1, max_length=100)
    monster_level: int = Field(ge=1)
    difficulty: str = Field(min_length=1, max_length=20)
    location_id: UUID
    reward_experience: int = Field(ge=0)
    reward_gold: int = Field(ge=0)


class StartCombatRequest(BaseModel):
    character_id: UUID
    encounter_definition_id: UUID
    seed: int = Field(ge=0, le=2_147_483_647)


class CombatActionRequest(BaseModel):
    combat_id: UUID
    action_type: Literal["ATTACK", "SKILL", "ITEM", "GUARD", "WAIT"]
    target_id: UUID | None = None
    skill_id: UUID | None = None
    inventory_item_id: UUID | None = None


class FleeCombatRequest(BaseModel):
    combat_id: UUID


class StatusEffectView(BaseModel):
    code: str
    duration: int
    potency: int


class CombatParticipantView(BaseModel):
    id: UUID
    source_id: UUID
    name: str = Field(min_length=1, max_length=100)
    side: Literal["PLAYER", "ENEMY"]
    level: int = Field(ge=1)
    current_hp: int = Field(ge=0)
    max_hp: int = Field(ge=1)
    current_mp: int = Field(ge=0)
    max_mp: int = Field(ge=0)
    current_stamina: int = Field(ge=0)
    max_stamina: int = Field(ge=0)
    guarding: bool
    defeated: bool
    statuses: list[StatusEffectView]


class CombatRewardView(BaseModel):
    experience: int = 0
    gold: int = 0
    items: list[str] = Field(default_factory=list)


class CombatLogView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sequence: int
    round_number: int
    action_type: str
    outcome: dict[str, object]
    text: str
    created_at: datetime


class CombatStateView(BaseModel):
    combat_id: UUID
    encounter_name: str
    seed: int
    status: Literal["ACTIVE", "VICTORY", "DEFEAT", "FLED"]
    round_number: int
    action_sequence: int
    turn_order: list[UUID]
    participants: list[CombatParticipantView]
    rewards: CombatRewardView
    recent_log: list[CombatLogView]
