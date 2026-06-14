from time import perf_counter
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.metrics import QDRANT_QUERY_DURATION_SECONDS
from app.models.memory import Memory
from app.rag.contracts import MemoryType, RetrievalQuery
from app.rag.errors import QdrantError

MEMORY_COLLECTIONS: dict[MemoryType, str] = {
    MemoryType.PLAYER: "player_memories",
    MemoryType.NPC: "npc_memories",
    MemoryType.FACTION: "faction_memories",
    MemoryType.QUEST: "quest_memories",
    MemoryType.LOCATION: "location_memories",
    MemoryType.WORLD: "world_memories",
    MemoryType.DIALOGUE: "dialogue_memories",
    MemoryType.ITEM: "item_memories",
    MemoryType.LORE: "lore_memories",
}


class QdrantPoint(BaseModel):
    """Minimal validated Qdrant search point."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: UUID
    score: float = Field(ge=-1, le=1)


class QdrantSearchResponse(BaseModel):
    """Validated Qdrant search response."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    result: tuple[QdrantPoint, ...]


class QdrantClient:
    """Small HTTP boundary for rebuildable vector-index operations."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        dimensions: int,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._dimensions = dimensions

    async def ensure_collection(self, memory_type: MemoryType) -> None:
        collection = MEMORY_COLLECTIONS[memory_type]
        try:
            response = await self._client.get(
                f"{self._base_url}/collections/{collection}"
            )
        except httpx.HTTPError as error:
            raise QdrantError("Qdrant collection lookup failed") from error
        if response.status_code == 200:
            return
        if response.status_code != 404:
            self._raise_error(response, "collection lookup")
        await self._request(
            "PUT",
            f"/collections/{collection}",
            {"vectors": {"size": self._dimensions, "distance": "Cosine"}},
        )

    async def upsert(self, memory: Memory, vector: list[float]) -> None:
        memory_type = MemoryType(memory.memory_type)
        await self.ensure_collection(memory_type)
        payload: dict[str, object] = {
            "points": [
                {
                    "id": str(memory.id),
                    "vector": vector,
                    "payload": {
                        "memory_id": str(memory.id),
                        "player_id": str(memory.player_id),
                        "memory_type": memory.memory_type,
                        "entity_type": memory.entity_type,
                        "entity_id": str(memory.entity_id),
                        "importance": memory.importance,
                        "tags": memory.tags,
                        "timestamp": memory.occurred_at.isoformat(),
                    },
                }
            ]
        }
        await self._request(
            "PUT",
            f"/collections/{MEMORY_COLLECTIONS[memory_type]}/points?wait=true",
            payload,
        )

    async def delete(self, memory: Memory) -> None:
        memory_type = MemoryType(memory.memory_type)
        await self.ensure_collection(memory_type)
        await self._request(
            "POST",
            f"/collections/{MEMORY_COLLECTIONS[memory_type]}/points/delete?wait=true",
            {"points": [str(memory.id)]},
        )

    async def search(
        self,
        memory_type: MemoryType,
        vector: list[float],
        query: RetrievalQuery,
    ) -> tuple[QdrantPoint, ...]:
        await self.ensure_collection(memory_type)
        must: list[object] = [
            {"key": "player_id", "match": {"value": str(query.player_id)}}
        ]
        if query.allowed_entity_ids:
            must.append(
                {
                    "key": "entity_id",
                    "match": {
                        "any": [
                            str(entity_id)
                            for entity_id in sorted(query.allowed_entity_ids, key=str)
                        ]
                    },
                }
            )
        must.extend(
            {"key": "tags", "match": {"value": tag}}
            for tag in sorted(query.required_tags)
        )
        must_not: list[object] = [
            {"key": "tags", "match": {"value": tag}}
            for tag in sorted(query.excluded_tags)
        ]
        payload: dict[str, object] = {
            "vector": vector,
            "limit": query.limit,
            "with_payload": False,
            "filter": {"must": must, "must_not": must_not},
        }
        started_at = perf_counter()
        data = await self._request(
            "POST",
            f"/collections/{MEMORY_COLLECTIONS[memory_type]}/points/search",
            payload,
        )
        QDRANT_QUERY_DURATION_SECONDS.observe(perf_counter() - started_at)
        try:
            return QdrantSearchResponse.model_validate(data).result
        except ValueError as error:
            raise QdrantError("Qdrant returned an invalid search response") from error

    async def recreate_collections(self) -> None:
        for memory_type, collection in MEMORY_COLLECTIONS.items():
            try:
                response = await self._client.delete(
                    f"{self._base_url}/collections/{collection}"
                )
            except httpx.HTTPError as error:
                raise QdrantError("Qdrant collection deletion failed") from error
            if response.status_code not in {200, 404}:
                self._raise_error(response, "collection deletion")
            await self.ensure_collection(memory_type)

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, object],
    ) -> object:
        try:
            response = await self._client.request(
                method,
                f"{self._base_url}{path}",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise QdrantError("Qdrant request failed") from error

    @staticmethod
    def _raise_error(response: httpx.Response, operation: str) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise QdrantError(f"Qdrant {operation} failed") from error
