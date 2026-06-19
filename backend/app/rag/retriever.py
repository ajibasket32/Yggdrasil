import math
from datetime import datetime
from uuid import UUID

from app.rag.cache import MemoryContextCache
from app.rag.contracts import (
    MemoryContextPackage,
    MemoryType,
    RetrievalQuery,
    RetrievedMemory,
)
from app.rag.embedding import DeterministicTextEmbedder
from app.rag.qdrant import QdrantClient
from app.repositories.memory import MemoryRepository


class MemoryRetriever:
    """Build bounded, provider-neutral context from scoped canonical memories."""

    def __init__(
        self,
        repository: MemoryRepository,
        embedder: DeterministicTextEmbedder,
        qdrant: QdrantClient,
        cache: MemoryContextCache,
    ) -> None:
        self._repository = repository
        self._embedder = embedder
        self._qdrant = qdrant
        self._cache = cache

    async def retrieve(self, query: RetrievalQuery) -> MemoryContextPackage:
        cached = await self._cache.get(query)
        if cached is not None:
            return cached

        vector = self._embedder.embed(query.query_text)
        relevance_by_id: dict[UUID, float] = {}
        for memory_type in query.memory_types:
            points = await self._qdrant.search(memory_type, vector, query)
            for point in points:
                relevance_by_id[point.id] = max(
                    relevance_by_id.get(point.id, 0),
                    min(1, max(0, point.score)),
                )

        memories = await self._repository.get_active_by_ids(
            query.player_id,
            list(relevance_by_id),
        )
        ranked: list[RetrievedMemory] = []
        for memory in memories:
            tags = frozenset(memory.tags)
            if query.allowed_entity_ids and memory.entity_id not in query.allowed_entity_ids:
                continue
            if not query.required_tags.issubset(tags):
                continue
            if query.excluded_tags.intersection(tags):
                continue
            relevance = relevance_by_id[memory.id]
            relationship = min(
                1,
                max(0, query.relationship_weights.get(memory.entity_id, 0)),
            )
            score = self.score(
                relevance=relevance,
                importance=memory.importance,
                occurred_at=memory.occurred_at,
                as_of=query.as_of,
                relationship_weight=relationship,
            )
            token_count = self.estimate_tokens(memory.summary)
            ranked.append(
                RetrievedMemory(
                    memory_id=memory.id,
                    memory_type=MemoryType(memory.memory_type),
                    entity_id=memory.entity_id,
                    entity_type=memory.entity_type,
                    summary=memory.summary,
                    importance=memory.importance,
                    occurred_at=memory.occurred_at,
                    tags=tuple(memory.tags),
                    relevance_score=relevance,
                    final_score=score,
                    estimated_tokens=token_count,
                )
            )
        ranked.sort(
            key=lambda item: (
                item.final_score,
                item.importance,
                item.occurred_at,
                str(item.memory_id),
            ),
            reverse=True,
        )

        selected: list[RetrievedMemory] = []
        total_tokens = 0
        truncated = len(ranked) > query.limit
        for candidate in ranked:
            if len(selected) >= query.limit:
                truncated = True
                break
            if total_tokens + candidate.estimated_tokens > query.max_context_tokens:
                truncated = True
                continue
            selected.append(candidate)
            total_tokens += candidate.estimated_tokens

        package = MemoryContextPackage(
            memories=tuple(selected),
            estimated_tokens=total_tokens,
            truncated=truncated,
            cache_hit=False,
        )
        await self._cache.set(query, package)
        return package

    @staticmethod
    def score(
        *,
        relevance: float,
        importance: int,
        occurred_at: datetime,
        as_of: datetime,
        relationship_weight: float,
    ) -> float:
        """Apply the canonical relevance/importance/recency/relationship formula."""
        age_seconds = max(0, (as_of - occurred_at).total_seconds())
        weeks = age_seconds / (7 * 24 * 60 * 60)
        recency = 1.0 if importance >= 8 else math.pow(0.9, weeks)
        result = (
            min(1, max(0, relevance)) * 0.4
            + (importance / 10) * 0.3
            + recency * 0.2
            + min(1, max(0, relationship_weight)) * 0.1
        )
        return min(1, max(0, result))

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Return a conservative provider-neutral token estimate."""
        return max(1, math.ceil(len(text.encode("utf-8")) / 4))
