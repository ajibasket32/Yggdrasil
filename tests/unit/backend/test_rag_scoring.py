from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.rag.contracts import MemoryContextPackage
from app.rag.embedding import DeterministicTextEmbedder
from app.rag.retriever import MemoryRetriever


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def test_embedding_is_deterministic_and_query_sensitive() -> None:
    embedder = DeterministicTextEmbedder()

    first = embedder.embed("ancient bridge guarded by knights")
    second = embedder.embed("ancient bridge guarded by knights")
    related = embedder.embed("knights guard the ancient bridge")
    unrelated = embedder.embed("merchant sells apples")

    assert first == second
    assert cosine(first, related) > cosine(first, unrelated)


def test_memory_score_matches_documented_formula_and_decay() -> None:
    now = datetime.now(UTC)

    recent = MemoryRetriever.score(
        relevance=0.5,
        importance=5,
        occurred_at=now,
        as_of=now,
        relationship_weight=0.5,
    )
    one_week_old = MemoryRetriever.score(
        relevance=0.5,
        importance=5,
        occurred_at=now - timedelta(days=7),
        as_of=now,
        relationship_weight=0.5,
    )
    legendary_old = MemoryRetriever.score(
        relevance=0.5,
        importance=8,
        occurred_at=now - timedelta(days=700),
        as_of=now,
        relationship_weight=0.5,
    )

    assert recent == pytest.approx(0.6)
    assert one_week_old == pytest.approx(0.58)
    assert legendary_old == pytest.approx(0.69)


def test_context_contract_rejects_gameplay_mutation_fields() -> None:
    with pytest.raises(ValidationError):
        MemoryContextPackage.model_validate(
            {
                "memories": [],
                "estimated_tokens": 0,
                "truncated": False,
                "cache_hit": False,
                "gold_reward": 100,
                "quest_state": "COMPLETED",
                "actor_id": str(uuid4()),
            }
        )
