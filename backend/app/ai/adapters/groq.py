import httpx

from app.ai.adapters.openai_compatible import OpenAICompatibleAdapter


class GroqAdapter(OpenAICompatibleAdapter):
    """Groq OpenAI-compatible adapter."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        model: str,
        base_url: str,
    ) -> None:
        super().__init__(
            client,
            name="groq",
            api_key=api_key,
            model=model,
            base_url=base_url,
        )
