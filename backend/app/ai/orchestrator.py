import asyncio
from time import perf_counter

from app.ai.contracts import (
    NarrativeRequest,
    NarrativeResult,
    RequestBudget,
)
from app.ai.errors import (
    BudgetUnavailableError,
    NarrativeValidationError,
    ProviderError,
)
from app.ai.registry import ProviderRegistration, ProviderRegistry
from app.ai.validation import NarrativeValidator
from app.core.logging import get_logger
from app.core.metrics import (
    AI_CACHED_TEMPLATE_USES_TOTAL,
    AI_FALLBACK_USES_TOTAL,
    AI_OUTPUT_REJECTIONS_TOTAL,
    AI_PROVIDER_FAILURES_TOTAL,
    AI_PROVIDER_LATENCY_SECONDS,
    AI_REQUESTS_TOTAL,
)


class AIOrchestrator:
    """Route narrative-only requests through bounded provider fallback."""

    def __init__(
        self,
        registry: ProviderRegistry,
        budget: RequestBudget,
        validator: NarrativeValidator,
        attempts_per_provider: int = 2,
    ) -> None:
        self._registry = registry
        self._budget = budget
        self._validator = validator
        self._attempts_per_provider = attempts_per_provider
        self._logger = get_logger()

    async def generate(self, request: NarrativeRequest) -> NarrativeResult:
        """Return validated narrative or approved cached content."""
        AI_REQUESTS_TOTAL.labels("attempt").inc()
        try:
            allowed = await self._budget.allow(request.actor_id)
        except BudgetUnavailableError:
            return await self._cached_result(request, "budget_unavailable")
        if not allowed:
            return await self._cached_result(request, "budget_exceeded")

        providers = self._registry.providers
        primary_name = next(
            (provider.name for provider in providers if provider.name != "cached"),
            "cached",
        )
        for registration in providers:
            if registration.name == "cached":
                return await self._cached_result(request, "providers_exhausted")
            result = await self._try_provider(
                request,
                registration,
                primary_name,
            )
            if result is not None:
                AI_REQUESTS_TOTAL.labels("success").inc()
                return result
        return await self._cached_result(request, "providers_exhausted")

    async def _try_provider(
        self,
        request: NarrativeRequest,
        registration: ProviderRegistration,
        primary_name: str,
    ) -> NarrativeResult | None:
        for attempt in range(1, self._attempts_per_provider + 1):
            started_at = perf_counter()
            try:
                async with asyncio.timeout(registration.timeout_seconds):
                    generation = await registration.adapter.generate(request)
                AI_PROVIDER_LATENCY_SECONDS.labels(registration.name).observe(
                    perf_counter() - started_at
                )
                output = self._validator.validate(request, generation)
                fallback_used = registration.name != primary_name
                if fallback_used:
                    AI_FALLBACK_USES_TOTAL.labels(registration.name).inc()
                self._logger.info(
                    "AI provider response accepted",
                    event_name="ai.provider.accepted",
                    category="AI",
                    provider=registration.name,
                    model=generation.model,
                    attempt=attempt,
                    fallback_used=fallback_used,
                )
                return NarrativeResult(
                    request_id=request.request_id,
                    provider=registration.name,
                    model=generation.model,
                    output=output,
                    fallback_used=fallback_used,
                    cached=False,
                )
            except NarrativeValidationError:
                AI_OUTPUT_REJECTIONS_TOTAL.labels(
                    registration.name,
                    "validation",
                ).inc()
                self._record_failure(registration.name, "validation", attempt)
                if attempt == self._attempts_per_provider:
                    return None
            except TimeoutError:
                self._record_failure(registration.name, "timeout", attempt)
            except ProviderError:
                self._record_failure(registration.name, "provider_error", attempt)
        return None

    async def _cached_result(
        self,
        request: NarrativeRequest,
        reason: str,
    ) -> NarrativeResult:
        registration = self._registry.providers[-1]
        generation = await registration.adapter.generate(request)
        output = self._validator.validate(request, generation)
        AI_CACHED_TEMPLATE_USES_TOTAL.labels(reason).inc()
        AI_REQUESTS_TOTAL.labels("cached").inc()
        self._logger.info(
            "Approved cached narrative used",
            event_name="ai.cached.used",
            category="AI",
            provider="cached",
            reason=reason,
        )
        return NarrativeResult(
            request_id=request.request_id,
            provider="cached",
            model=generation.model,
            output=output,
            fallback_used=True,
            cached=True,
        )

    def _record_failure(self, provider: str, reason: str, attempt: int) -> None:
        AI_PROVIDER_FAILURES_TOTAL.labels(provider, reason).inc()
        self._logger.warning(
            "AI provider attempt failed",
            event_name="ai.provider.failed",
            category="AI",
            provider=provider,
            error_code=reason,
            attempt=attempt,
        )
