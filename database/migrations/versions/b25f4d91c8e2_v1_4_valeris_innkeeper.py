"""Move the innkeeper service into Valeris City.

Revision ID: b25f4d91c8e2
Revises: a14c2f8b7e91
Create Date: 2026-06-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision: str = "b25f4d91c8e2"
down_revision: str | None = "a14c2f8b7e91"
branch_labels: str | None = None
depends_on: str | None = None

ELENA_ID = "74000000-0000-0000-0000-000000000008"
VALERIS_ID = "56000000-0000-0000-0000-000000000005"
GREENWOOD_ID = "56000000-0000-0000-0000-000000000002"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE npcs
            SET home_location_id = CAST(:valeris_id AS UUID),
                schedule = '[{"start_hour": 0, "end_hour": 24, "location_id": "56000000-0000-0000-0000-000000000005"}]'::jsonb
            WHERE id = CAST(:elena_id AS UUID)
            """
        ).bindparams(elena_id=ELENA_ID, valeris_id=VALERIS_ID)
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE npcs
            SET home_location_id = CAST(:greenwood_id AS UUID),
                schedule = '[{"start_hour": 0, "end_hour": 24, "location_id": "56000000-0000-0000-0000-000000000002"}]'::jsonb
            WHERE id = CAST(:elena_id AS UUID)
            """
        ).bindparams(elena_id=ELENA_ID, greenwood_id=GREENWOOD_ID)
    )
