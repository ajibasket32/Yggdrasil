import httpx
from pydantic import JsonValue

from app.ai.adapters.base import HttpAdapter
from app.ai.contracts import NarrativeRequest, ProviderGeneration
from app.ai.prompt import provider_system_prompt


class OllamaAdapter(HttpAdapter):
    """Local Ollama structured-generation adapter."""

    name = "ollama"

    def __init__(
        self,
        client: httpx.AsyncClient,
        model: str,
        base_url: str,
    ) -> None:
        super().__init__(client)
        self._model = model
        self._base_url = base_url.rstrip("/")

    async def generate(self, request: NarrativeRequest) -> ProviderGeneration:
        payload: dict[str, JsonValue] = {
            "model": self._model,
            "prompt": request.instruction,
            "system": provider_system_prompt(),
            "format": "json",
            "stream": False,
            "options": {"num_predict": request.max_output_tokens},
        }
        data = await self._post(
            f"{self._base_url}/api/generate",
            payload=payload,
        )
        content = self._string(data.get("response"), "response")
        input_tokens = self._integer(data.get("prompt_eval_count"), "prompt_eval_count")
        output_tokens = self._integer(data.get("eval_count"), "eval_count")
        model = self._string(data.get("model", self._model), "model")
        return ProviderGeneration(
            provider=self.name,
            model=model,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
