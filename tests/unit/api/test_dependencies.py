from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_combat_service
from app.services.combat import CombatService


def test_get_combat_service() -> None:
    session = MagicMock(spec=AsyncSession)
    service = get_combat_service(session)
    assert isinstance(service, CombatService)
