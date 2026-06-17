import httpx
from pydantic import JsonValue

from app.ai.adapters.base import HttpAdapter
from app.ai.contracts import NarrativeRequest, ProviderGeneration
from app.ai.errors import ProviderError
from app.ai.prompt import provider_system_prompt


class GeminiAdapter(HttpAdapter):
    """Google Gemini generateContent adapter."""

    name = "gemini"

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
            "systemInstruction": {
                "parts": [{"text": provider_system_prompt()}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": request.instruction}],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": request.max_output_tokens,
            },
        }
        data = await self._post(
            f"{self._base_url}/models/{self._model}:generateContent",
            headers={"x-goog-api-key": self._api_key},
            payload=payload,
        )
        candidates = self._list(data.get("candidates"), "candidates")
        if not candidates:
            raise ProviderError("gemini returned no candidates")
        candidate = self._dictionary(candidates[0], "candidate")
        content = self._dictionary(candidate.get("content"), "content")
        parts = self._list(content.get("parts"), "parts")
        if not parts:
            raise ProviderError("gemini returned no content parts")
        part = self._dictionary(parts[0], "part")
        text = self._string(part.get("text"), "text")
        usage = self._dictionary(data.get("usageMetadata", {}), "usageMetadata")
        input_tokens = self._integer(usage.get("promptTokenCount"), "promptTokenCount")
        output_tokens = self._integer(usage.get("candidatesTokenCount"), "candidatesTokenCount")
        return ProviderGeneration(
            provider=self.name,
            model=self._model,
            content=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
