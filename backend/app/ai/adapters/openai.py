import httpx

from app.ai.adapters.openai_compatible import OpenAICompatibleAdapter


class OpenAIAdapter(OpenAICompatibleAdapter):
    """OpenAI chat-completions adapter."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        model: str,
        base_url: str,
    ) -> None:
        super().__init__(
            client,
            name="openai",
            api_key=api_key,
            model=model,
            base_url=base_url,
        )
