import json
from functools import lru_cache
from pathlib import Path

from pydantic import JsonValue

from app.ai.contracts import NarrativeRequest, ProviderGeneration
from app.ai.errors import ProviderError

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "cached_narrative.json"


@lru_cache
def _templates() -> dict[str, JsonValue]:
    data = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ProviderError("Cached narrative template file is invalid")
    return data


class CachedNarrativeAdapter:
    """Approved local narrative fallback with no network dependency."""

    name = "cached"

    async def generate(self, request: NarrativeRequest) -> ProviderGeneration:
        template = _templates().get(request.kind.value)
        if not isinstance(template, dict):
            raise ProviderError("No cached narrative exists for this request kind")
        return ProviderGeneration(
            provider=self.name,
            model="cached-narrative-v1",
            content=json.dumps(template, separators=(",", ":"), sort_keys=True),
        )
