from datetime import UTC, datetime
from uuid import uuid4

from app.ai.context import NarrativeContext, NarrativeMemory
from app.ai.contracts import NarrativeKind
from app.ai.prompt_builder import NarrativePromptBuilder


def context() -> NarrativeContext:
    character_id = uuid4()
    location_id = uuid4()
    memory_id = uuid4()
    return NarrativeContext(
        character_id=character_id,
        character_name="Aster Vale",
        location_id=location_id,
        location_name="Greenwood Verge",
        memories=(
            NarrativeMemory(
                id=memory_id,
                memory_type="NPC_MEMORY",
                entity_id=uuid4(),
                summary="Aster offered aid to the frontier warden.",
                importance=6,
                occurred_at=datetime(2026, 6, 14, tzinfo=UTC),
            ),
        ),
        allowed_entity_ids=frozenset({character_id, location_id}),
    )


def test_context_hash_is_stable_for_identical_canonical_data() -> None:
    value = context()

    assert value.content_hash() == value.model_copy().content_hash()
    reversed_ids = tuple(reversed(tuple(value.allowed_entity_ids)))
    assert (
        value.content_hash()
        == value.model_copy(
            update={"allowed_entity_ids": frozenset(reversed_ids)}
        ).content_hash()
    )


def test_prompt_is_versioned_and_contains_bounded_context() -> None:
    instruction, version = NarrativePromptBuilder().build(
        NarrativeKind.DESCRIPTION,
        context(),
        "LOCATION_DESCRIPTION",
    )

    assert version == "location-description-v1"
    assert "CANONICAL CONTEXT JSON" in instruction
    assert "Greenwood Verge" in instruction
    assert "PLAYER MENU CHOICE\n\nLOCATION_DESCRIPTION" in instruction
