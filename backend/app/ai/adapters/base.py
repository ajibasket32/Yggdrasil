import httpx
from pydantic import JsonValue

from app.ai.errors import ProviderError


class HttpAdapter:
    """Shared HTTP behavior for provider-specific adapter files."""

    name: str

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def _post(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        payload: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        try:
            response = await self._client.post(
                url,
                headers=headers,
                params=params,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise ProviderError(f"{self.name} request failed") from error
        if not isinstance(data, dict):
            raise ProviderError(f"{self.name} returned an invalid response body")
        return data

    def _dictionary(self, value: JsonValue, field: str) -> dict[str, JsonValue]:
        if not isinstance(value, dict):
            raise ProviderError(f"{self.name} returned invalid {field}")
        return value

    def _list(self, value: JsonValue, field: str) -> list[JsonValue]:
        if not isinstance(value, list):
            raise ProviderError(f"{self.name} returned invalid {field}")
        return value

    def _string(self, value: JsonValue, field: str) -> str:
        if not isinstance(value, str):
            raise ProviderError(f"{self.name} returned invalid {field}")
        return value

    def _integer(self, value: JsonValue | None, field: str) -> int:
        if not isinstance(value, int):
            if value is None:
                return 0
            raise ProviderError(f"{self.name} returned invalid {field}")
        return value
