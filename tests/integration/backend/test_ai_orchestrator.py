import asyncio
import json
from uuid import UUID, uuid4

import pytest

from app.ai.adapters.cached import CachedNarrativeAdapter
from app.ai.contracts import NarrativeKind, NarrativeRequest, ProviderGeneration
from app.ai.errors import BudgetUnavailableError, ProviderError
from app.ai.orchestrator import AIOrchestrator
from app.ai.registry import ProviderRegistration, ProviderRegistry
from app.ai.validation import NarrativeValidator


class AllowBudget:
    async def allow(self, actor_id: UUID) -> bool:
        return True


class DenyBudget:
    async def allow(self, actor_id: UUID) -> bool:
        return False


class UnavailableBudget:
    async def allow(self, actor_id: UUID) -> bool:
        raise BudgetUnavailableError("redis unavailable")


class StubAdapter:
    def __init__(
        self,
        name: str,
        *,
        error: bool = False,
        delay: float = 0,
        text: str = "A measured response.",
    ) -> None:
        self.name = name
        self.error = error
        self.delay = delay
        self.text = text
        self.calls = 0

    async def generate(self, request: NarrativeRequest) -> ProviderGeneration:
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise ProviderError(f"{self.name} unavailable")
        return ProviderGeneration(
            provider=self.name,
            model=f"{self.name}-test",
            content=json.dumps(
                {
                    "text": self.text,
                    "tone": "neutral",
                    "tags": [],
                    "referenced_entity_ids": [],
                }
            ),
        )


def request() -> NarrativeRequest:
    return NarrativeRequest(
        actor_id=uuid4(),
        kind=NarrativeKind.DIALOGUE,
        instruction="Offer a greeting.",
    )


def orchestrator(
    adapters: list[StubAdapter],
    budget: AllowBudget | DenyBudget | UnavailableBudget | None = None,
    *,
    attempts: int = 1,
    timeout: float = 0.05,
) -> AIOrchestrator:
    registrations = [ProviderRegistration(adapter.name, adapter, timeout) for adapter in adapters]
    registrations.append(ProviderRegistration("cached", CachedNarrativeAdapter(), timeout))
    return AIOrchestrator(
        ProviderRegistry(tuple(registrations)),
        budget or AllowBudget(),
        NarrativeValidator(),
        attempts_per_provider=attempts,
    )


@pytest.mark.asyncio
async def test_provider_failure_advances_to_next_provider() -> None:
    first = StubAdapter("gemini", error=True)
    second = StubAdapter("groq")

    result = await orchestrator([first, second]).generate(request())

    assert result.provider == "groq"
    assert result.fallback_used is True
    assert first.calls == 1
    assert second.calls == 1


@pytest.mark.asyncio
async def test_timeout_advances_to_next_provider() -> None:
    result = await orchestrator([StubAdapter("gemini", delay=0.1), StubAdapter("groq")]).generate(
        request()
    )

    assert result.provider == "groq"


@pytest.mark.asyncio
async def test_invalid_output_retries_then_advances() -> None:
    invalid = StubAdapter("gemini", text="damage: 900")
    valid = StubAdapter("groq")

    result = await orchestrator([invalid, valid], attempts=2).generate(request())

    assert invalid.calls == 2
    assert result.provider == "groq"


@pytest.mark.asyncio
async def test_all_six_network_providers_fall_back_to_cached_content() -> None:
    names = ["gemini", "groq", "openai", "anthropic", "openrouter", "ollama"]
    adapters = [StubAdapter(name, error=True) for name in names]

    result = await orchestrator(adapters).generate(request())

    assert result.provider == "cached"
    assert result.cached is True
    assert all(adapter.calls == 1 for adapter in adapters)


@pytest.mark.asyncio
@pytest.mark.parametrize("budget", [DenyBudget(), UnavailableBudget()])
async def test_budget_failure_uses_cached_content(
    budget: DenyBudget | UnavailableBudget,
) -> None:
    provider = StubAdapter("gemini")

    result = await orchestrator([provider], budget).generate(request())

    assert result.provider == "cached"
    assert provider.calls == 0
