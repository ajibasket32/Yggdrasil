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


def upgrade() -> None:
    op.execute(sa.text("UPDATE locations SET is_starting_location = false"))
    op.execute(
        sa.text(
            "UPDATE locations SET is_starting_location = true WHERE id = CAST(:id AS UUID)"
        ).bindparams(id=VALERIS_CITY_ID)
    )


def downgrade() -> None:
    op.execute(sa.text("UPDATE locations SET is_starting_location = false"))
    op.execute(
        sa.text(
            "UPDATE locations SET is_starting_location = true WHERE id = CAST(:id AS UUID)"
        ).bindparams(id=VALERIS_OUTSKIRTS_ID)
    )
