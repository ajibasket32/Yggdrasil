from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, EntityMixin


class Memory(EntityMixin, Base):
    """Canonical, player-scoped world memory stored before vector indexing."""

    __tablename__ = "memories"
    __table_args__ = (
        CheckConstraint(
            "importance BETWEEN 1 AND 10",
            name="ck_memories_importance",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'DELETED')",
            name="ck_memories_status",
        ),
        CheckConstraint(
            "index_status IN ('PENDING', 'INDEXED', 'FAILED', 'DELETED')",
            name="ck_memories_index_status",
        ),
        Index(
            "uq_memories_active_content",
            "player_id",
            "memory_type",
            "entity_type",
            "entity_id",
            "content_hash",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    player_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    memory_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    source_entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_entity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    world_event_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )
    entity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    participants: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    location_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    index_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MemoryLink(EntityMixin, Base):
    """Typed directed link between two canonical memories."""

    __tablename__ = "memory_links"
    __table_args__ = (
        UniqueConstraint(
            "memory_a_id",
            "memory_b_id",
            "relationship_type",
            name="uq_memory_links_relationship",
        ),
        CheckConstraint(
            "memory_a_id <> memory_b_id",
            name="ck_memory_links_distinct_memories",
        ),
    )

    memory_a_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_b_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(String(40), nullable=False)


class MemoryIndexJob(EntityMixin, Base):
    """Durable, retryable request to synchronize one memory with Qdrant."""

    __tablename__ = "memory_index_jobs"
    __table_args__ = (
        CheckConstraint(
            "operation IN ('UPSERT', 'DELETE')",
            name="ck_memory_index_jobs_operation",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'RETRY', 'COMPLETED', 'FAILED')",
            name="ck_memory_index_jobs_status",
        ),
        CheckConstraint(
            "attempts >= 0 AND max_attempts > 0",
            name="ck_memory_index_jobs_attempts",
        ),
        Index(
            "ix_memory_index_jobs_due",
            "status",
            "next_attempt_at",
        ),
    )

    memory_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
