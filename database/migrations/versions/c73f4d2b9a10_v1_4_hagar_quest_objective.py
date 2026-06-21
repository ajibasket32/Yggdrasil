"""Retarget the blacksmith quest service objective to Hagar.

Revision ID: c73f4d2b9a10
Revises: b25f4d91c8e2
Create Date: 2026-06-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision: str = "c73f4d2b9a10"
down_revision: str | None = "b25f4d91c8e2"
branch_labels: str | None = None
depends_on: str | None = None

HAGAR_ID = "74000000-0000-0000-0000-000000000006"
SILAS_ID = "74000000-0000-0000-0000-000000000002"
QUEST_BLACKSMITH_ID = "75000000-0000-0000-0000-000000000008"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE quest_steps
            SET target_id = CAST(:hagar_id AS UUID),
                description = 'Buy a Steel Sword from Hagar for testing.'
            WHERE quest_id = CAST(:quest_id AS UUID)
              AND sequence = 1
              AND description = 'Buy a Steel Sword from Silas for testing.'
            """
        ).bindparams(hagar_id=HAGAR_ID, quest_id=QUEST_BLACKSMITH_ID)
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE quest_steps
            SET target_id = CAST(:silas_id AS UUID),
                description = 'Buy a Steel Sword from Silas for testing.'
            WHERE quest_id = CAST(:quest_id AS UUID)
              AND sequence = 1
              AND description = 'Buy a Steel Sword from Hagar for testing.'
            """
        ).bindparams(silas_id=SILAS_ID, quest_id=QUEST_BLACKSMITH_ID)
    )
