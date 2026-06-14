from datetime import datetime
from uuid import UUID

from pydantic import JsonValue
from sqlalchemy import BigInteger, DateTime, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, EntityMixin


class SaveGame(EntityMixin, Base):
    """One complete, versioned, atomic game-state snapshot."""

    __tablename__ = "save_games"

    player_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    character_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    save_name: Mapped[str] = mapped_column(String(120), nullable=False)
    save_version: Mapped[int] = mapped_column(Integer, nullable=False)
    world_tick: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    snapshot_reference: Mapped[dict[str, JsonValue]] = mapped_column(
        JSONB, nullable=False
    )
    snapshot_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
