import json
from uuid import uuid4

import httpx
import pytest

from app.ai.adapters import (
    AnthropicAdapter,
    GeminiAdapter,
    GroqAdapter,
    OllamaAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
)
from app.ai.contracts import NarrativeKind, NarrativeRequest
from app.ai.registry import build_provider_registry
from app.core.config import Settings


def narrative_request() -> NarrativeRequest:
    return NarrativeRequest(
        actor_id=uuid4(),
        kind=NarrativeKind.NARRATION,
        instruction="Describe a quiet road.",
    )


def response_payload() -> str:
    return json.dumps(
        {
            "text": "The road lies quiet beneath a gray sky.",
            "tone": "calm",
            "tags": ["road"],
            "referenced_entity_ids": [],
        }
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("adapter_type", "provider"),
    [
        (OpenAIAdapter, "openai"),
        (GroqAdapter, "groq"),
        (OpenRouterAdapter, "openrouter"),
    ],
)
async def test_openai_compatible_adapters_map_chat_completions(
    adapter_type: type[OpenAIAdapter],
    provider: str,
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        body = json.loads(request.content)
        assert body["response_format"] == {"type": "json_object"}
        assert body["messages"][0]["role"] == "system"
        return httpx.Response(
            200,
            json={
                "model": "configured-model",
                "choices": [{"message": {"content": response_payload()}}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 7},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = adapter_type(
            client, "secret", "configured-model", "https://ai.test/v1"
        )
        result = await adapter.generate(narrative_request())

    assert result.provider == provider
    assert result.output_tokens == 7


@pytest.mark.asyncio
async def test_gemini_adapter_maps_generate_content() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/models/gemini-test:generateContent")
        assert request.headers["x-goog-api-key"] == "secret"
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": response_payload()}]}}],
                "usageMetadata": {
                    "promptTokenCount": 3,
                    "candidatesTokenCount": 6,
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GeminiAdapter(
            client, "secret", "gemini-test", "https://gemini.test/v1beta"
        ).generate(narrative_request())

    assert result.provider == "gemini"
    assert result.output_tokens == 6


@pytest.mark.asyncio
async def test_anthropic_adapter_maps_messages() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/messages")
        assert request.headers["anthropic-version"] == "2023-06-01"
        return httpx.Response(
            200,
            json={
                "model": "claude-test",
                "content": [{"type": "text", "text": response_payload()}],
                "usage": {"input_tokens": 2, "output_tokens": 5},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await AnthropicAdapter(
            client, "secret", "claude-test", "https://anthropic.test/v1"
        ).generate(narrative_request())

    assert result.provider == "anthropic"
    assert result.output_tokens == 5


@pytest.mark.asyncio
async def test_ollama_adapter_maps_local_generation() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        return httpx.Response(
            200,
            json={
                "model": "local-test",
                "response": response_payload(),
                "prompt_eval_count": 2,
                "eval_count": 4,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await OllamaAdapter(
            client, "local-test", "http://ollama.test"
        ).generate(narrative_request())

    assert result.provider == "ollama"
    assert result.output_tokens == 4


@pytest.mark.asyncio
async def test_registry_skips_unconfigured_providers_and_ends_with_cached() -> None:
    settings = Settings(
        ai_provider_order="gemini,openai,ollama,cached",
        openai_api_key="secret",
        openai_model="openai-test",
    )
    async with httpx.AsyncClient() as client:
        registry = build_provider_registry(settings, client)

    assert [provider.name for provider in registry.providers] == [
        "openai",
        "cached",
    ]
