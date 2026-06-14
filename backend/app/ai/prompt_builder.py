from functools import lru_cache
from pathlib import Path

from app.ai.context import NarrativeContext
from app.ai.contracts import NarrativeKind

PROMPT_ROOT = Path(__file__).parent / "prompts"
PROMPT_FILES = {
    NarrativeKind.DIALOGUE: ("dialogue/npc_dialogue_v1.txt", "npc-dialogue-v1"),
    NarrativeKind.LORE: ("lore/entity_lore_v1.txt", "entity-lore-v1"),
    NarrativeKind.NARRATION: (
        "narration/quest_framing_v1.txt",
        "quest-framing-v1",
    ),
    NarrativeKind.DESCRIPTION: (
        "lore/location_description_v1.txt",
        "location-description-v1",
    ),
}


@lru_cache
def _prompt(relative_path: str) -> str:
    return (PROMPT_ROOT / relative_path).read_text(encoding="utf-8")


class NarrativePromptBuilder:
    """Build versioned prompts from bounded canonical context."""

    def build(
        self,
        kind: NarrativeKind,
        context: NarrativeContext,
        topic_id: str,
    ) -> tuple[str, str]:
        """Return provider instruction and immutable prompt version."""
        relative_path, version = PROMPT_FILES[kind]
        instruction = "\n\n".join(
            (
                _prompt(relative_path).strip(),
                "CANONICAL CONTEXT JSON",
                context.model_dump_json(),
                "PLAYER MENU CHOICE",
                topic_id,
            )
        )
        return instruction, version
