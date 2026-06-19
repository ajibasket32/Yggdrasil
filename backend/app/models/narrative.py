from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, EntityMixin


class NarrativeRecord(EntityMixin, Base):
    """Validated cosmetic narrative stored outside canonical gameplay state."""

    __tablename__ = "narrative_records"
    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "kind",
            "request_key",
            name="uq_narrative_records_request",
        ),
        Index(
            "ix_narrative_records_context",
            "player_id",
            "character_id",
            "kind",
            "entity_id",
            "context_hash",
            "prompt_version",
        ),
    )

    player_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    character_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    npc_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("npcs.id"), nullable=True, index=True
    )
    entity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    topic_id: Mapped[str] = mapped_column(String(40), nullable=False)
    request_key: Mapped[str] = mapped_column(String(200), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False)
    context_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    model: Mapped[str] = mapped_column(String(160), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str] = mapped_column(String(40), nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    referenced_entity_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
