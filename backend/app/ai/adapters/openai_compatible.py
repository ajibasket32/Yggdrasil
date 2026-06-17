import httpx
from pydantic import JsonValue

from app.ai.adapters.base import HttpAdapter
from app.ai.contracts import NarrativeRequest, ProviderGeneration
from app.ai.errors import ProviderError
from app.ai.prompt import provider_system_prompt


class OpenAICompatibleAdapter(HttpAdapter):
    """Shared adapter for OpenAI-compatible chat-completions APIs."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        name: str,
        api_key: str,
        model: str,
        base_url: str,
    ) -> None:
        super().__init__(client)
        self.name = name
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    async def generate(self, request: NarrativeRequest) -> ProviderGeneration:
        payload: dict[str, JsonValue] = {
            "model": self._model,
            "max_tokens": request.max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": provider_system_prompt()},
                {"role": "user", "content": request.instruction},
            ],
        }
        data = await self._post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            payload=payload,
        )
        choices = self._list(data.get("choices"), "choices")
        if not choices:
            raise ProviderError(f"{self.name} returned no choices")
        choice = self._dictionary(choices[0], "choice")
        message = self._dictionary(choice.get("message"), "message")
        content = self._string(message.get("content"), "content")
        usage = self._dictionary(data.get("usage", {}), "usage")
        input_tokens = self._integer(usage.get("prompt_tokens"), "prompt_tokens")
        output_tokens = self._integer(
            usage.get("completion_tokens"), "completion_tokens"
        )
        model = self._string(data.get("model", self._model), "model")
        return ProviderGeneration(
            provider=self.name,
            model=model,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
