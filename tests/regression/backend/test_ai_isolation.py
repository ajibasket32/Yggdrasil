import inspect
from uuid import uuid4

import pytest

from app.ai.contracts import NarrativeKind, NarrativeOutput, NarrativeRequest, ProviderGeneration
from app.ai.errors import ProviderError
from app.ai.orchestrator import AIOrchestrator
from app.ai.prompt import provider_system_prompt
from app.ai.registry import ProviderRegistration, ProviderRegistry
from app.ai.validation import NarrativeValidator


class AllowBudget:
    async def allow(self, actor_id: object) -> bool:
        return True


class SecretErrorAdapter:
    name = "openai"

    async def generate(self, request: NarrativeRequest) -> ProviderGeneration:
        raise ProviderError("Bearer super-secret-provider-key")


class CachedAdapter:
    name = "cached"

    async def generate(self, request: NarrativeRequest) -> ProviderGeneration:
        from app.ai.adapters.cached import CachedNarrativeAdapter

        return await CachedNarrativeAdapter().generate(request)


def test_narrative_contract_has_no_gameplay_mutation_fields() -> None:
    fields = set(NarrativeOutput.model_fields)
    forbidden = {
        "damage",
        "xp",
        "gold",
        "loot",
        "quest_state",
        "world_state",
        "inventory",
        "stats",
        "rewards",
    }

    assert fields.isdisjoint(forbidden)


def test_provider_prompt_denies_gameplay_authority() -> None:
    prompt = provider_system_prompt().lower()

    assert "do not calculate" in prompt
    assert "gameplay state changed" in prompt
    assert "return one json object" in prompt


def test_orchestrator_has_no_game_state_dependency() -> None:
    source = inspect.getsource(AIOrchestrator)

    assert "SaveGame" not in source
    assert "AsyncSession" not in source
    assert "repositories" not in source


@pytest.mark.asyncio
async def test_provider_error_details_are_not_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    registry = ProviderRegistry(
        (
            ProviderRegistration("openai", SecretErrorAdapter(), 1),
            ProviderRegistration("cached", CachedAdapter(), 1),
        )
    )
    orchestrator = AIOrchestrator(
        registry,
        AllowBudget(),
        NarrativeValidator(),
        attempts_per_provider=1,
    )
    request = NarrativeRequest(
        actor_id=uuid4(),
        kind=NarrativeKind.LORE,
        instruction="Describe an old stone.",
    )

    result = await orchestrator.generate(request)
    log_text = "\n".join(record.getMessage() for record in caplog.records)

    assert result.provider == "cached"
    assert "super-secret-provider-key" not in log_text
