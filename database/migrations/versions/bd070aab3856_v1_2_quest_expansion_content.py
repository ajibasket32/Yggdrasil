"""v1.2 quest expansion content

Revision ID: bd070aab3856
Revises: e1bd0d4d29d7
Create Date: 2026-06-19 08:14:16.890666
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "bd070aab3856"
down_revision: str | None = "e1bd0d4d29d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# IDs
VALERIS_ID = "56000000-0000-0000-0000-000000000005"
GREENWOOD_ID = "56000000-0000-0000-0000-000000000002"
HAGAR_ID = "74000000-0000-0000-0000-000000000006"
KAEL_ID = "74000000-0000-0000-0000-000000000007"
QUEST_BLACKSMITH_ID = "75000000-0000-0000-0000-000000000008"
QUEST_SCOUT_ID = "75000000-0000-0000-0000-000000000009"
SYLVAN_BRANCH_ID = "56000000-0000-0000-0000-000000000006"
SILAS_ID = "74000000-0000-0000-0000-000000000002"
SHOP_SILAS_ID = "80000000-0000-0000-0000-000000000001"
ITEM_STEEL_SWORD_ID = "54000000-0000-0000-0000-000000000011"


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    # Adding quest objectives for the quests defined in the previous migration
    # "The Blacksmith's Request" (QUEST_BLACKSMITH_ID)
    # Objective 1: Speak with Hagar (Sequence 0, NPC_HELP) -> Already added in previous migration
    # Objective 2: Buy a Steel Sword from Silas (Sequence 1, NPC_HELP since we don't have SHOP_BUY yet as a type)
    op.execute(
        sa.text(
            "INSERT INTO quest_steps (id, quest_id, sequence, objective_type, target_id, description, required_count) "
            "VALUES (uuid_generate_v4(), :quest, 1, 'NPC_HELP', :silas, 'Buy a Steel Sword from Silas for testing.', 1)"
        ).bindparams(quest=QUEST_BLACKSMITH_ID, silas=SILAS_ID)
    )

    # "Scouting the Border" (QUEST_SCOUT_ID)
    # Objective 2: Reach the Deepwood Marker (Sequence 1, LOCATION_DISCOVERY)
    op.execute(
        sa.text(
            "INSERT INTO quest_steps (id, quest_id, sequence, objective_type, target_id, description, required_count) "
            "VALUES (uuid_generate_v4(), :quest, 1, 'LOCATION_DISCOVERY', :loc, 'Scout the further reaches of the Sylvan Branch.', 1)"
        ).bindparams(quest=QUEST_SCOUT_ID, loc=SYLVAN_BRANCH_ID)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM quest_steps WHERE quest_id IN (:q1, :q2) AND sequence > 0").bindparams(
            q1=QUEST_BLACKSMITH_ID, q2=QUEST_SCOUT_ID
        )
    )
