"""Move the blacksmith shop service to Hagar.

Revision ID: a14c2f8b7e91
Revises: f3b1a7c9d204
Create Date: 2026-06-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision: str = "a14c2f8b7e91"
down_revision: str | None = "f3b1a7c9d204"
branch_labels: str | None = None
depends_on: str | None = None

HAGAR_ID = "74000000-0000-0000-0000-000000000006"
SILAS_ID = "74000000-0000-0000-0000-000000000002"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE shops
            SET owner_npc_id = CAST(:hagar_id AS UUID),
                name = 'Hagar''s Forge',
                description = 'Hagar sells dependable arms and tools from his Valeris forge.'
            WHERE owner_npc_id = CAST(:silas_id AS UUID)
            """
        ).bindparams(hagar_id=HAGAR_ID, silas_id=SILAS_ID)
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE shops
            SET owner_npc_id = CAST(:silas_id AS UUID),
                name = 'Silas''s Sundries',
                description = 'Silas offers various wares for the traveling adventurer.'
            WHERE owner_npc_id = CAST(:hagar_id AS UUID)
            """
        ).bindparams(hagar_id=HAGAR_ID, silas_id=SILAS_ID)
    )
