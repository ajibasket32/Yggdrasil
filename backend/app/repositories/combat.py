from types import TracebackType
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.models.combat import (
    CombatEncounter,
    CombatLogEntry,
    CombatParticipant,
    EncounterDefinition,
    GameOutboxEvent,
    Monster,
)
from app.repositories.gameplay import (
    CharacterRepository,
    DefinitionRepository,
    EquipmentRepository,
    InventoryRepository,
)
from app.repositories.save import IdempotencyRepository


class CombatRepository:
    """Canonical encounter, participant, log, and outbox persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_definitions(
        self, location_id: UUID
    ) -> list[tuple[EncounterDefinition, Monster]]:
        result = await self._session.execute(
            select(EncounterDefinition, Monster)
            .join(Monster, Monster.id == EncounterDefinition.monster_id)
            .where(
                EncounterDefinition.location_id == location_id,
                EncounterDefinition.enabled.is_(True),
            )
            .order_by(EncounterDefinition.name)
        )
        return list(result.tuples().all())

    async def get_definition(
        self, definition_id: UUID
    ) -> tuple[EncounterDefinition, Monster] | None:
        result = await self._session.execute(
            select(EncounterDefinition, Monster)
            .join(Monster, Monster.id == EncounterDefinition.monster_id)
            .where(EncounterDefinition.id == definition_id)
        )
        return result.tuples().one_or_none()

    async def active_for_character(
        self, character_id: UUID, *, for_update: bool = False
    ) -> CombatEncounter | None:
        statement = select(CombatEncounter).where(
            CombatEncounter.character_id == character_id,
            CombatEncounter.status == "ACTIVE",
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_owned(
        self,
        player_id: UUID,
        encounter_id: UUID,
        *,
        for_update: bool = False,
    ) -> CombatEncounter | None:
        statement = select(CombatEncounter).where(
            CombatEncounter.id == encounter_id,
            CombatEncounter.player_id == player_id,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def add_encounter(self, encounter: CombatEncounter) -> CombatEncounter:
        self._session.add(encounter)
        await self._session.flush()
        return encounter

    async def add_participant(self, participant: CombatParticipant) -> CombatParticipant:
        self._session.add(participant)
        await self._session.flush()
        return participant

    async def participants(
        self, encounter_id: UUID, *, for_update: bool = False
    ) -> list[CombatParticipant]:
        statement = (
            select(CombatParticipant)
            .where(CombatParticipant.encounter_id == encounter_id)
            .order_by(CombatParticipant.side.desc(), CombatParticipant.id)
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def logs(self, encounter_id: UUID, *, limit: int | None = None) -> list[CombatLogEntry]:
        statement = (
            select(CombatLogEntry)
            .where(CombatLogEntry.encounter_id == encounter_id)
            .order_by(CombatLogEntry.sequence)
        )
        if limit is not None:
            statement = statement.limit(limit)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def add_log(self, entry: CombatLogEntry) -> CombatLogEntry:
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def add_event(self, event: GameOutboxEvent) -> GameOutboxEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def flush(self) -> None:
        await self._session.flush()


class CombatUnitOfWork:
    """Own one atomic v0.6 combat transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self.combat = CombatRepository(session)
        self.characters = CharacterRepository(session)
        self.definitions = DefinitionRepository(session)
        self.inventory = InventoryRepository(session)
        self.equipment = EquipmentRepository(session)
        self.idempotency = IdempotencyRepository(session)
        self._session = session
        self._transaction: AsyncSessionTransaction | None = None

    async def __aenter__(self) -> "CombatUnitOfWork":
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        return self

    async def lock_key(self, value: str) -> None:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:value, 0))"),
            {"value": value},
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._transaction is None:
            raise RuntimeError("CombatUnitOfWork exited before it was entered")
        await self._transaction.__aexit__(exc_type, exc_value, traceback)
