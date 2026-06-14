import hashlib
import json
from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import UUID

from pydantic import JsonValue, ValidationError

from app.core.metrics import (
    LOAD_DURATION_SECONDS,
    SAVE_ATTEMPTS_TOTAL,
    SAVE_DURATION_SECONDS,
    SAVE_FAILURES_TOTAL,
    SAVE_MIGRATIONS_TOTAL,
    SAVE_OPERATIONS_TOTAL,
)
from app.models.idempotency_record import IdempotencyRecord
from app.models.save_game import SaveGame
from app.repositories.gameplay import CanonicalSnapshot, GameStateRepository
from app.repositories.save import SaveUnitOfWork
from app.schemas.save import (
    CURRENT_SAVE_SCHEMA_VERSION,
    ENGINE_VERSION,
    DeleteSaveResult,
    LoadedSave,
    SaveSnapshotV1,
    SaveSummary,
)


class SaveError(Exception):
    """Base error for save workflow failures."""


class SaveNotFoundError(SaveError):
    """The requested save does not exist for the current player."""


class SaveIntegrityError(SaveError):
    """The persisted snapshot failed checksum or schema validation."""


class SaveCompatibilityError(SaveError):
    """The save schema cannot be migrated by this release."""


class IdempotencyConflictError(SaveError):
    """An idempotency key was reused with a different request."""


class RecoveryPointError(SaveError):
    """Deletion would remove the only verified recovery point."""


class SaveActiveCombatError(SaveError):
    """A save mutation would conflict with an active combat encounter."""


class SaveMigrator:
    """Migrate supported historical snapshot versions to the current contract."""

    @staticmethod
    def migrate(
        snapshot: dict[str, JsonValue],
        schema_version: int,
    ) -> SaveSnapshotV1:
        if schema_version == CURRENT_SAVE_SCHEMA_VERSION:
            try:
                return SaveSnapshotV1.model_validate(snapshot)
            except ValidationError as error:
                raise SaveIntegrityError("Save snapshot schema is invalid") from error

        if schema_version == 0:
            migrated: dict[str, JsonValue] = {
                "schema_version": 1,
                "world_tick": snapshot.get("world_tick", 0),
                "character": snapshot.get(
                    "character",
                    snapshot.get("character_state", {}),
                ),
                "inventory": snapshot.get("inventory", {}),
                "equipment": snapshot.get("equipment", {}),
                "world_state": snapshot.get(
                    "world_state",
                    snapshot.get("world", {}),
                ),
                "quest_state": snapshot.get("quest_state", {}),
                "npc_state": snapshot.get("npc_state", {}),
                "faction_state": snapshot.get("faction_state", {}),
                "relationships": snapshot.get("relationships", {}),
                "journal": snapshot.get("journal", {}),
                "memories": snapshot.get("memories", {}),
                "dungeon_state": snapshot.get("dungeon_state", {}),
            }
            try:
                return SaveSnapshotV1.model_validate(migrated)
            except ValidationError as error:
                raise SaveCompatibilityError(
                    "Legacy save version 0 could not be migrated"
                ) from error

        raise SaveCompatibilityError(
            f"Save schema version {schema_version} is unsupported; "
            f"supported versions are 0 and {CURRENT_SAVE_SCHEMA_VERSION}"
        )


class SaveService:
    """Coordinate atomic, versioned save operations through repositories."""

    def __init__(
        self,
        unit_of_work: SaveUnitOfWork,
        game_state: GameStateRepository | None = None,
    ) -> None:
        self._uow = unit_of_work
        self._game_state = game_state

    async def create_save(
        self,
        player_id: UUID,
        character_id: UUID,
        save_name: str | None,
        idempotency_key: str,
        snapshot: SaveSnapshotV1 | None = None,
    ) -> SaveSummary:
        started_at = perf_counter()
        SAVE_ATTEMPTS_TOTAL.labels("create").inc()
        operation = "save.create"

        async with self._uow:
            if (
                self._game_state is not None
                and await self._game_state.has_active_combat(player_id, character_id)
            ):
                SAVE_FAILURES_TOTAL.labels("create", "active_combat").inc()
                raise SaveActiveCombatError(
                    "Cannot create a save while combat is active"
                )
            canonical_snapshot = snapshot
            if canonical_snapshot is None and self._game_state is not None:
                captured = await self._game_state.capture(player_id, character_id)
                if captured is not None:
                    canonical_snapshot = SaveSnapshotV1(
                        character=captured.character,
                        inventory=captured.inventory,
                        equipment=captured.equipment,
                        world_state=captured.world_state,
                        quest_state=captured.quest_state,
                        npc_state=captured.npc_state,
                        faction_state=captured.faction_state,
                        relationships=captured.relationships,
                        journal=captured.journal,
                        memories=captured.memories,
                        dungeon_state=captured.dungeon_state,
                    )
            canonical_snapshot = canonical_snapshot or SaveSnapshotV1()
            payload = canonical_snapshot.model_dump(mode="json")
            fingerprint = self._fingerprint(
                {
                    "character_id": str(character_id),
                    "save_name": save_name,
                    "snapshot": payload,
                }
            )
            await self._uow.saves.lock_key(
                f"idempotency:{player_id}:{operation}:{idempotency_key}"
            )
            existing = await self._uow.idempotency.get(
                player_id, idempotency_key, operation
            )
            if existing is not None:
                self._assert_same_fingerprint(existing, fingerprint)
                summary = await self._summary_from_idempotency(player_id, existing)
                SAVE_DURATION_SECONDS.observe(perf_counter() - started_at)
                return summary

            save_version = await self._uow.saves.next_version(player_id, character_id)
            save = SaveGame(
                player_id=player_id,
                character_id=character_id,
                save_name=save_name or f"Save {save_version}",
                save_version=save_version,
                world_tick=canonical_snapshot.world_tick,
                snapshot_reference=payload,
                snapshot_checksum=self.checksum(payload),
                schema_version=CURRENT_SAVE_SCHEMA_VERSION,
                engine_version=ENGINE_VERSION,
                status="VERIFIED",
            )
            await self._uow.saves.add(save)
            await self._record_idempotency(
                player_id,
                idempotency_key,
                fingerprint,
                operation,
                201,
                {"save_id": str(save.id)},
            )
            SAVE_OPERATIONS_TOTAL.labels("create", "success").inc()
            SAVE_DURATION_SECONDS.observe(perf_counter() - started_at)
            return self._summary(save)

    async def list_saves(self, player_id: UUID) -> list[SaveSummary]:
        async with self._uow:
            saves = await self._uow.saves.list_active(player_id)
            return [self._summary(save) for save in saves]

    async def load_save(
        self,
        player_id: UUID,
        save_id: UUID,
        idempotency_key: str,
    ) -> LoadedSave:
        started_at = perf_counter()
        SAVE_ATTEMPTS_TOTAL.labels("load").inc()
        fingerprint = self._fingerprint({"save_id": str(save_id)})
        operation = "save.load"

        async with self._uow:
            await self._uow.saves.lock_key(
                f"idempotency:{player_id}:{operation}:{idempotency_key}"
            )
            existing = await self._uow.idempotency.get(
                player_id, idempotency_key, operation
            )
            if existing is not None:
                self._assert_same_fingerprint(existing, fingerprint)
                stored_id = UUID(str(existing.response_body["save_id"]))
                loaded = await self._load_owned_save(player_id, stored_id)
                LOAD_DURATION_SECONDS.observe(perf_counter() - started_at)
                return loaded

            loaded = await self._load_owned_save(player_id, save_id, for_update=True)
            await self._record_idempotency(
                player_id,
                idempotency_key,
                fingerprint,
                operation,
                200,
                {"save_id": str(save_id)},
            )
            SAVE_OPERATIONS_TOTAL.labels("load", "success").inc()
            LOAD_DURATION_SECONDS.observe(perf_counter() - started_at)
            return loaded

    async def delete_save(
        self,
        player_id: UUID,
        save_id: UUID,
        idempotency_key: str,
    ) -> DeleteSaveResult:
        SAVE_ATTEMPTS_TOTAL.labels("delete").inc()
        fingerprint = self._fingerprint({"save_id": str(save_id)})
        operation = "save.delete"

        async with self._uow:
            await self._uow.saves.lock_key(
                f"idempotency:{player_id}:{operation}:{idempotency_key}"
            )
            existing = await self._uow.idempotency.get(
                player_id, idempotency_key, operation
            )
            if existing is not None:
                self._assert_same_fingerprint(existing, fingerprint)
                return DeleteSaveResult(save_id=save_id, deleted=True)

            save = await self._uow.saves.get(
                player_id,
                save_id,
                include_deleted=True,
                for_update=True,
            )
            if save is None:
                raise SaveNotFoundError("Save was not found")
            if save.deleted_at is not None:
                result = DeleteSaveResult(save_id=save_id, deleted=True)
            else:
                if (
                    save.status == "VERIFIED"
                    and not await self._uow.saves.has_other_verified(save)
                    and await self._uow.saves.has_newer_unverified(save)
                ):
                    SAVE_FAILURES_TOTAL.labels(
                        "delete", "recovery_point_required"
                    ).inc()
                    raise RecoveryPointError(
                        "Cannot delete the only verified recovery point while "
                        "a newer save is unverified"
                    )
                self._uow.saves.soft_delete(save)
                result = DeleteSaveResult(save_id=save_id, deleted=True)

            await self._record_idempotency(
                player_id,
                idempotency_key,
                fingerprint,
                operation,
                200,
                {"save_id": str(save_id), "deleted": True},
            )
            SAVE_OPERATIONS_TOTAL.labels("delete", "success").inc()
            return result

    async def _load_owned_save(
        self,
        player_id: UUID,
        save_id: UUID,
        *,
        for_update: bool = False,
    ) -> LoadedSave:
        save = await self._uow.saves.get(
            player_id,
            save_id,
            for_update=for_update,
        )
        if save is None:
            SAVE_FAILURES_TOTAL.labels("load", "not_found").inc()
            raise SaveNotFoundError("Save was not found")
        if self._game_state is not None and await self._game_state.has_active_combat(
            player_id, save.character_id
        ):
            SAVE_FAILURES_TOTAL.labels("load", "active_combat").inc()
            raise SaveActiveCombatError("Cannot load a save while combat is active")
        if self.checksum(save.snapshot_reference) != save.snapshot_checksum:
            SAVE_OPERATIONS_TOTAL.labels("load", "integrity_failure").inc()
            SAVE_FAILURES_TOTAL.labels("load", "integrity").inc()
            raise SaveIntegrityError("Save checksum validation failed")

        try:
            snapshot = SaveMigrator.migrate(
                save.snapshot_reference,
                save.schema_version,
            )
        except (SaveCompatibilityError, SaveIntegrityError):
            SAVE_FAILURES_TOTAL.labels("load", "compatibility").inc()
            raise
        if save.schema_version != CURRENT_SAVE_SCHEMA_VERSION:
            source_version = save.schema_version
            migrated_payload = snapshot.model_dump(mode="json")
            save.snapshot_reference = migrated_payload
            save.snapshot_checksum = self.checksum(migrated_payload)
            save.schema_version = CURRENT_SAVE_SCHEMA_VERSION
            save.engine_version = ENGINE_VERSION
            save.world_tick = snapshot.world_tick
            SAVE_MIGRATIONS_TOTAL.labels(
                str(source_version),
                str(CURRENT_SAVE_SCHEMA_VERSION),
                "success",
            ).inc()

        if self._game_state is not None and snapshot.character.get("id"):
            try:
                await self._game_state.restore(
                    player_id,
                    save.character_id,
                    CanonicalSnapshot(
                        character=snapshot.character,
                        inventory=snapshot.inventory,
                        equipment=snapshot.equipment,
                        world_state=snapshot.world_state,
                        quest_state=snapshot.quest_state,
                        npc_state=snapshot.npc_state,
                        faction_state=snapshot.faction_state,
                        relationships=snapshot.relationships,
                        journal=snapshot.journal,
                        memories=snapshot.memories,
                        dungeon_state=snapshot.dungeon_state,
                    ),
                )
            except (KeyError, TypeError, ValueError) as error:
                SAVE_FAILURES_TOTAL.labels("load", "game_state_invalid").inc()
                raise SaveIntegrityError(
                    "Saved canonical gameplay state is invalid"
                ) from error

        return LoadedSave(**self._summary(save).model_dump(), snapshot=snapshot)

    async def _summary_from_idempotency(
        self,
        player_id: UUID,
        record: IdempotencyRecord,
    ) -> SaveSummary:
        save_id = UUID(str(record.response_body["save_id"]))
        save = await self._uow.saves.get(player_id, save_id)
        if save is None:
            raise SaveIntegrityError("Stored idempotency result references no save")
        return self._summary(save)

    async def _record_idempotency(
        self,
        player_id: UUID,
        key: str,
        fingerprint: str,
        operation: str,
        status: int,
        body: dict[str, JsonValue],
    ) -> None:
        await self._uow.idempotency.add(
            IdempotencyRecord(
                player_id=player_id,
                idempotency_key=key,
                request_fingerprint=fingerprint,
                operation=operation,
                response_status=status,
                response_body=body,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )

    @staticmethod
    def checksum(snapshot: dict[str, JsonValue]) -> str:
        """Return a deterministic SHA-256 checksum for a JSON snapshot."""
        serialized = json.dumps(
            snapshot,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def _fingerprint(payload: dict[str, JsonValue]) -> str:
        return SaveService.checksum(payload)

    @staticmethod
    def _assert_same_fingerprint(
        record: IdempotencyRecord,
        fingerprint: str,
    ) -> None:
        if record.request_fingerprint != fingerprint:
            raise IdempotencyConflictError(
                "Idempotency key was already used with a different request"
            )

    @staticmethod
    def _summary(save: SaveGame) -> SaveSummary:
        return SaveSummary(
            save_id=save.id,
            character_id=save.character_id,
            save_name=save.save_name,
            save_version=save.save_version,
            world_tick=save.world_tick,
            schema_version=save.schema_version,
            engine_version=save.engine_version,
            status=save.status,
            created_at=save.created_at,
        )
