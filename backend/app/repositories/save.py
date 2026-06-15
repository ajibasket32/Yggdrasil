from datetime import UTC, datetime
from types import TracebackType
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.models.idempotency_record import IdempotencyRecord
from app.models.save_game import SaveGame


class SaveRepository:
    """PostgreSQL access for complete save snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock_key(self, value: str) -> None:
        """Serialize operations sharing one logical transaction key."""
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:value, 0))"),
            {"value": value},
        )

    async def next_version(self, player_id: UUID, character_id: UUID) -> int:
        """Return the next per-character save version under an advisory lock."""
        await self.lock_key(f"save-version:{player_id}:{character_id}")
        result = await self._session.execute(
            select(func.coalesce(func.max(SaveGame.save_version), 0)).where(
                SaveGame.player_id == player_id,
                SaveGame.character_id == character_id,
            )
        )
        return int(result.scalar_one()) + 1

    async def add(self, save: SaveGame) -> SaveGame:
        """Stage and flush one complete snapshot."""
        self._session.add(save)
        await self._session.flush()
        return save

    async def get(
        self,
        player_id: UUID,
        save_id: UUID,
        *,
        include_deleted: bool = False,
        for_update: bool = False,
    ) -> SaveGame | None:
        """Read one owned save, optionally locking it for mutation."""
        statement = select(SaveGame).where(
            SaveGame.id == save_id,
            SaveGame.player_id == player_id,
        )
        if not include_deleted:
            statement = statement.where(SaveGame.deleted_at.is_(None))
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_active(self, player_id: UUID) -> list[SaveGame]:
        """List active saves newest first."""
        result = await self._session.execute(
            select(SaveGame)
            .where(
                SaveGame.player_id == player_id,
                SaveGame.deleted_at.is_(None),
            )
            .order_by(SaveGame.created_at.desc())
        )
        return list(result.scalars().all())

    async def has_newer_unverified(self, save: SaveGame) -> bool:
        """Return whether an active, newer, unverified save exists."""
        result = await self._session.execute(
            select(func.count())
            .select_from(SaveGame)
            .where(
                SaveGame.player_id == save.player_id,
                SaveGame.created_at > save.created_at,
                SaveGame.status != "VERIFIED",
                SaveGame.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one()) > 0

    async def has_other_verified(self, save: SaveGame) -> bool:
        """Return whether another active verified recovery point exists."""
        result = await self._session.execute(
            select(func.count())
            .select_from(SaveGame)
            .where(
                SaveGame.player_id == save.player_id,
                SaveGame.id != save.id,
                SaveGame.status == "VERIFIED",
                SaveGame.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one()) > 0

    @staticmethod
    def soft_delete(save: SaveGame) -> None:
        """Mark a save deleted while preserving recovery data."""
        save.deleted_at = datetime.now(UTC)


class IdempotencyRepository:
    """PostgreSQL access for retry-safe mutation outcomes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        player_id: UUID,
        key: str,
        operation: str,
    ) -> IdempotencyRecord | None:
        """Read one idempotency record by player and key."""
        result = await self._session.execute(
            select(IdempotencyRecord).where(
                IdempotencyRecord.player_id == player_id,
                IdempotencyRecord.idempotency_key == key,
                IdempotencyRecord.operation == operation,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, record: IdempotencyRecord) -> None:
        self._session.add(record)
        await self._session.flush()


class SaveUnitOfWork:
    """Own one database transaction and its save repositories."""

    def __init__(self, session: AsyncSession) -> None:
        self.saves = SaveRepository(session)
        self.idempotency = IdempotencyRepository(session)
        self._session = session
        self._transaction: AsyncSessionTransaction | None = None

    async def __aenter__(self) -> "SaveUnitOfWork":
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._transaction is None:
            raise RuntimeError("SaveUnitOfWork exited before it was entered")
        await self._transaction.__aexit__(exc_type, exc_value, traceback)
