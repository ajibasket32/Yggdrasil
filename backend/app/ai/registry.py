from dataclasses import dataclass

import httpx

from app.ai.adapters import (
    AnthropicAdapter,
    CachedNarrativeAdapter,
    GeminiAdapter,
    GroqAdapter,
    OllamaAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
)
from app.ai.contracts import ProviderAdapter
from app.ai.errors import ProviderConfigurationError
from app.core.config import Settings

KNOWN_PROVIDERS = {
    "gemini",
    "groq",
    "openai",
    "anthropic",
    "openrouter",
    "ollama",
    "cached",
}


@dataclass(frozen=True)
class ProviderRegistration:
    """One configured adapter and its request timeout."""

    name: str
    adapter: ProviderAdapter
    timeout_seconds: float


class ProviderRegistry:
    """Ordered, immutable provider fallback registry."""

    def __init__(self, providers: tuple[ProviderRegistration, ...]) -> None:
        if not providers or providers[-1].name != "cached":
            raise ProviderConfigurationError(
                "The cached narrative adapter must be the final provider"
            )
        self.providers = providers


def build_provider_registry(
    settings: Settings,
    client: httpx.AsyncClient,
) -> ProviderRegistry:
    """Build configured adapters in the declared fallback order."""
    unknown = set(settings.provider_order) - KNOWN_PROVIDERS
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ProviderConfigurationError(f"Unknown AI providers: {names}")
    if len(settings.provider_order) != len(set(settings.provider_order)):
        raise ProviderConfigurationError("AI provider order contains duplicates")
    if not settings.provider_order or settings.provider_order[-1] != "cached":
        raise ProviderConfigurationError("AI provider order must end with cached")

    providers: list[ProviderRegistration] = []
    for name in settings.provider_order:
        adapter = _build_adapter(name, settings, client)
        if adapter is None:
            continue
        timeout = (
            settings.ai_local_timeout_seconds
            if name in {"ollama", "cached"}
            else settings.ai_cloud_timeout_seconds
        )
        providers.append(
            ProviderRegistration(
                name=name,
                adapter=adapter,
                timeout_seconds=timeout,
            )
        )
    return ProviderRegistry(tuple(providers))


def _build_adapter(
    name: str,
    settings: Settings,
    client: httpx.AsyncClient,
) -> ProviderAdapter | None:
    if name == "cached":
        return CachedNarrativeAdapter()
    if name == "ollama":
        if not settings.ollama_model:
            return None
        return OllamaAdapter(
            client,
            settings.ollama_model,
            settings.ollama_url,
        )

    api_key = getattr(settings, f"{name}_api_key").get_secret_value()
    model = getattr(settings, f"{name}_model")
    if not api_key or not model:
        return None
    base_url = getattr(settings, f"{name}_base_url")
    if name == "gemini":
        return GeminiAdapter(client, api_key, model, base_url)
    if name == "groq":
        return GroqAdapter(client, api_key, model, base_url)
    if name == "openai":
        return OpenAIAdapter(client, api_key, model, base_url)
    if name == "anthropic":
        return AnthropicAdapter(client, api_key, model, base_url)
    if name == "openrouter":
        return OpenRouterAdapter(client, api_key, model, base_url)
    raise ProviderConfigurationError(f"Unsupported AI provider: {name}")
