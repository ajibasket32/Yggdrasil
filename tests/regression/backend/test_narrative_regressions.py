from uuid import UUID, uuid4

import pytest

from app.ai.adapters.cached import CachedNarrativeAdapter
from app.ai.contracts import NarrativeKind, NarrativeRequest, ProviderGeneration
from app.ai.errors import ProviderError
from app.ai.orchestrator import AIOrchestrator
from app.ai.registry import ProviderRegistration, ProviderRegistry
from app.ai.validation import NarrativeValidator


class AllowBudget:
    async def allow(self, actor_id: UUID) -> bool:
        return True


class StateChangingAdapter:
    name = "unsafe"

    async def generate(self, request: NarrativeRequest) -> ProviderGeneration:
        return ProviderGeneration(
            provider=self.name,
            model="unsafe-model",
            content=(
                '{"text":"The quest state changed to completed.",'
                '"tone":"neutral","tags":[],"referenced_entity_ids":[]}'
            ),
        )


class OfflineAdapter:
    name = "offline"

    async def generate(self, request: NarrativeRequest) -> ProviderGeneration:
        raise ProviderError("provider unavailable")


@pytest.mark.asyncio
async def test_state_changing_or_offline_output_falls_back_to_safe_narrative() -> None:
    request = NarrativeRequest(
        actor_id=uuid4(),
        kind=NarrativeKind.DIALOGUE,
        instruction="Use canonical context for a fixed greeting topic.",
    )
    orchestrator = AIOrchestrator(
        ProviderRegistry(
            (
                ProviderRegistration("unsafe", StateChangingAdapter(), 0.1),
                ProviderRegistration("offline", OfflineAdapter(), 0.1),
                ProviderRegistration("cached", CachedNarrativeAdapter(), 0.1),
            )
        ),
        AllowBudget(),
        NarrativeValidator(),
        attempts_per_provider=1,
    )

    result = await orchestrator.generate(request)

    assert result.provider == "cached"
    assert result.fallback_used
    assert result.cached
    assert "quest state changed" not in result.output.text.lower()
