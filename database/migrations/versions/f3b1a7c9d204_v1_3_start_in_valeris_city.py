"""Start new characters in Valeris City.

Revision ID: f3b1a7c9d204
Revises: bd070aab3856
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3b1a7c9d204"
down_revision: str | None = "bd070aab3856"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

VALERIS_OUTSKIRTS_ID = "56000000-0000-0000-0000-000000000001"
VALERIS_CITY_ID = "56000000-0000-0000-0000-000000000005"
GREENWOOD_ID = "56000000-0000-0000-0000-000000000002"


def upgrade() -> None:
    op.execute(sa.text("UPDATE locations SET is_starting_location = false"))
    op.execute(
        sa.text(
            "UPDATE locations SET is_starting_location = true WHERE id = CAST(:id AS UUID)"
        ).bindparams(id=VALERIS_CITY_ID)
    )
    op.execute(
        sa.text(
            """
            INSERT INTO location_routes
                (origin_location_id, destination_location_id, travel_cost, requirements)
            VALUES
                (CAST(:city AS UUID), CAST(:greenwood AS UUID), 1, '{}'::jsonb),
                (CAST(:greenwood AS UUID), CAST(:city AS UUID), 1, '{}'::jsonb)
            ON CONFLICT (origin_location_id, destination_location_id) DO NOTHING
            """
        ).bindparams(city=VALERIS_CITY_ID, greenwood=GREENWOOD_ID)
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM location_routes
            WHERE
                (origin_location_id = CAST(:city AS UUID)
                    AND destination_location_id = CAST(:greenwood AS UUID))
                OR
                (origin_location_id = CAST(:greenwood AS UUID)
                    AND destination_location_id = CAST(:city AS UUID))
            """
        ).bindparams(city=VALERIS_CITY_ID, greenwood=GREENWOOD_ID)
    )
    op.execute(sa.text("UPDATE locations SET is_starting_location = false"))
    op.execute(
        sa.text(
            "UPDATE locations SET is_starting_location = true WHERE id = CAST(:id AS UUID)"
        ).bindparams(id=VALERIS_OUTSKIRTS_ID)
    )
