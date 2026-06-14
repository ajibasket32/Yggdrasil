from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError

from app.core.database import session_factory
from app.models.save_game import SaveGame
from app.repositories.save import SaveUnitOfWork
from app.schemas.save import SaveSnapshotV1
from app.services.save import (
    RecoveryPointError,
    SaveIntegrityError,
    SaveService,
)


@pytest.mark.asyncio
async def test_save_atomicity_rolls_back_when_final_write_fails(
    clean_save_database: None,
) -> None:
    async with session_factory() as session:
        service = SaveService(SaveUnitOfWork(session))
        with pytest.raises(DBAPIError):
            await service.create_save(
                uuid4(),
                uuid4(),
                "Must Roll Back",
                "x" * 201,
            )

    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(SaveGame))
    assert count == 0


@pytest.mark.asyncio
async def test_corrupt_snapshot_fails_closed(
    clean_save_database: None,
) -> None:
    player_id = uuid4()
    async with session_factory() as session:
        created = await SaveService(SaveUnitOfWork(session)).create_save(
            player_id,
            uuid4(),
            "Corrupt",
            "create-corrupt",
            SaveSnapshotV1(world_tick=10),
        )

    async with session_factory() as session:
        save = await session.get(SaveGame, created.save_id)
        assert save is not None
        save.snapshot_reference = {
            **save.snapshot_reference,
            "world_tick": 999,
        }
        await session.commit()

    async with session_factory() as session:
        with pytest.raises(SaveIntegrityError, match="checksum"):
            await SaveService(SaveUnitOfWork(session)).load_save(
                player_id,
                created.save_id,
                "load-corrupt",
            )


@pytest.mark.asyncio
async def test_only_verified_recovery_point_cannot_be_deleted(
    clean_save_database: None,
) -> None:
    player_id = uuid4()
    payload = SaveSnapshotV1().model_dump(mode="json")
    checksum = SaveService.checksum(payload)
    old_created_at = datetime.now(UTC) - timedelta(days=1)

    async with session_factory() as session:
        verified = SaveGame(
            player_id=player_id,
            character_id=uuid4(),
            save_name="Verified",
            save_version=1,
            world_tick=0,
            snapshot_reference=payload,
            snapshot_checksum=checksum,
            schema_version=1,
            engine_version="0.2.0",
            status="VERIFIED",
            created_at=old_created_at,
            updated_at=old_created_at,
        )
        unverified = SaveGame(
            player_id=player_id,
            character_id=uuid4(),
            save_name="Unverified",
            save_version=1,
            world_tick=0,
            snapshot_reference=payload,
            snapshot_checksum=checksum,
            schema_version=1,
            engine_version="0.2.0",
            status="UNVERIFIED",
        )
        session.add_all([verified, unverified])
        await session.commit()
        verified_id = verified.id

    async with session_factory() as session:
        with pytest.raises(RecoveryPointError):
            await SaveService(SaveUnitOfWork(session)).delete_save(
                player_id,
                verified_id,
                "delete-recovery",
            )

    async with session_factory() as session:
        retained = await session.get(SaveGame, verified_id)
    assert retained is not None
    assert retained.deleted_at is None
