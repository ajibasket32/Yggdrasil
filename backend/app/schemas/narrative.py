from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

DialogueTopic = Literal["GREETING", "QUEST", "LOCAL_NEWS", "FAREWELL"]
LoreEntityType = Literal["quest", "location"]


class DialogueRequest(BaseModel):
    character_id: UUID
    topic_id: DialogueTopic


class LoreRequest(BaseModel):
    character_id: UUID
    entity_id: UUID
    entity_type: LoreEntityType


class QuestFramingRequest(BaseModel):
    character_id: UUID


class LocationDescriptionRequest(BaseModel):
    character_id: UUID


class NarrativeView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    speaker_name: str | None
    text: str
    tone: str
    tags: list[str]
    fallback_used: bool
    cached: bool
    prompt_version: str
    context_memory_count: int
    available_topics: list[DialogueTopic]
