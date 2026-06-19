"""v1.2 quest expansion content

Revision ID: bd070aab3856
Revises: e1bd0d4d29d7
Create Date: 2026-06-19 08:14:16.890666
"""

from collections.abc import Sequence
from uuid import UUID

from alembic import op
import sqlalchemy as sa


revision: str = "bd070aab3856"
down_revision: str | None = "e1bd0d4d29d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# IDs
SILAS_ID = UUID("74000000-0000-0000-0000-000000000002")
QUEST_BLACKSMITH_ID = UUID("75000000-0000-0000-0000-000000000008")
QUEST_SCOUT_ID = UUID("75000000-0000-0000-0000-000000000009")
SYLVAN_BRANCH_ID = UUID("56000000-0000-0000-0000-000000000006")


def upgrade() -> None:
    # "The Blacksmith's Request" (QUEST_BLACKSMITH_ID)
    # Objective 2: Buy a Steel Sword from Silas
    op.execute(
        sa.text(
            "INSERT INTO quest_steps (id, quest_id, sequence, objective_type, target_id, description, required_count) "
            "VALUES (uuid_generate_v4(), :quest, 1, 'NPC_HELP', :silas, 'Buy a Steel Sword from Silas for testing.', 1)"
        ).bindparams(quest=QUEST_BLACKSMITH_ID, silas=SILAS_ID)
    )

    # "Scouting the Border" (QUEST_SCOUT_ID)
    # Objective 2: Reach the Deepwood Marker
    op.execute(
        sa.text(
            "INSERT INTO quest_steps (id, quest_id, sequence, objective_type, target_id, description, required_count) "
            "VALUES (uuid_generate_v4(), :quest, 1, 'LOCATION_DISCOVERY', :loc, 'Scout the further reaches of the Sylvan Branch.', 1)"
        ).bindparams(quest=QUEST_SCOUT_ID, loc=SYLVAN_BRANCH_ID)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM quest_steps WHERE quest_id IN (CAST(:q1 AS UUID), CAST(:q2 AS UUID)) AND sequence > 0").bindparams(
            q1=QUEST_BLACKSMITH_ID, q2=QUEST_SCOUT_ID
        )
    )
