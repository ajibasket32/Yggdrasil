"""Align canonical greenwood location display name with test contract.

Revision ID: 0008_greenwood_name
Revises: 0007_ai_narrative
Create Date: 2026-06-15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008_greenwood_name"
down_revision: str | None = "0007_ai_narrative"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Use the canonical service-facing name expected by gameplay flows."""
    op.execute("""
        UPDATE locations
        SET name = 'Greenwood Verge'
        WHERE id = '56000000-0000-0000-0000-000000000002'
        """)


def downgrade() -> None:
    """Restore the previous seed name on rollback."""
    op.execute("""
        UPDATE locations
        SET name = 'Valerian Forest'
        WHERE id = '56000000-0000-0000-0000-000000000002'
        """)
