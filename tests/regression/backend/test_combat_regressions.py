from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.core.database import session_factory
from app.repositories.combat import CombatUnitOfWork
from app.repositories.gameplay import GameUnitOfWork
from app.schemas.combat import StartCombatRequest
from app.schemas.gameplay import CreateCharacterRequest
from app.services.combat import CombatNotFoundError, CombatService
from app.services.gameplay import CharacterService


async def _ready_character(player_id: UUID):
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        definitions = await service.creation_definitions()
        character = await service.create_character(
            player_id,
            CreateCharacterRequest(
                name="Boundary Hero",
                race_id=definitions.races[0].id,
                gender="Unspecified",
                alignment="NEUTRAL",
                starting_job_id=definitions.starting_jobs[0].id,
            ),
            f"create-{player_id}",
        )
    async with session_factory() as session:
        service = CharacterService(GameUnitOfWork(session))
        locations = await service.locations(player_id, character.id)
        greenwood = next(
            value for value in locations if value.name == "Greenwood Verge"
        )
        await service.travel(
            player_id, character.id, greenwood.id, f"travel-{player_id}"
        )
    return character


@pytest.mark.asyncio
async def test_cross_player_combat_access_is_rejected(
    clean_gameplay_database: None,
) -> None:
    owner = uuid4()
    character = await _ready_character(owner)
    async with session_factory() as session:
        service = CombatService(CombatUnitOfWork(session))
        definition = (await service.available_encounters(owner, character.id))[0]
        state = await service.start(
            owner,
            StartCombatRequest(
                character_id=character.id,
                encounter_definition_id=definition.id,
                seed=5,
            ),
            "owner-start",
        )
    async with session_factory() as session:
        with pytest.raises(CombatNotFoundError):
            await CombatService(CombatUnitOfWork(session)).get(uuid4(), state.combat_id)


def test_combat_engine_has_no_ai_or_network_dependency() -> None:
    path = Path(__file__).parents[3] / "backend" / "app" / "engines" / "combat.py"
    source = path.read_text(encoding="utf-8")

    assert "app.ai" not in source
    assert "httpx" not in source
    assert "requests" not in source
