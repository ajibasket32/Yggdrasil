import httpx
from pydantic import JsonValue

from app.ai.adapters.base import HttpAdapter
from app.ai.contracts import NarrativeRequest, ProviderGeneration
from app.ai.errors import ProviderError
from app.ai.prompt import provider_system_prompt


class AnthropicAdapter(HttpAdapter):
    """Anthropic Messages adapter."""

    name = "anthropic"

    def __init__(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        model: str,
        base_url: str,
    ) -> None:
        super().__init__(client)
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    async def generate(self, request: NarrativeRequest) -> ProviderGeneration:
        payload: dict[str, JsonValue] = {
            "model": self._model,
            "max_tokens": request.max_output_tokens,
            "system": provider_system_prompt(),
            "messages": [{"role": "user", "content": request.instruction}],
        }
        data = await self._post(
            f"{self._base_url}/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
            payload=payload,
        )
        content_blocks = self._list(data.get("content"), "content")
        if not content_blocks:
            raise ProviderError("anthropic returned no content blocks")
        content_block = self._dictionary(content_blocks[0], "content block")
        content = self._string(content_block.get("text"), "text")
        usage = self._dictionary(data.get("usage", {}), "usage")
        input_tokens = self._integer(usage.get("input_tokens"), "input_tokens")
        output_tokens = self._integer(usage.get("output_tokens"), "output_tokens")
        model = self._string(data.get("model", self._model), "model")
        return ProviderGeneration(
            provider=self.name,
            model=model,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
