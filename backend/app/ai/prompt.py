from functools import lru_cache
from pathlib import Path

PROMPT_PATH = Path(__file__).parent / "prompts" / "provider" / "narrative_v1.txt"


@lru_cache
def provider_system_prompt() -> str:
    """Load the versioned provider prompt from disk."""
    return PROMPT_PATH.read_text(encoding="utf-8")
