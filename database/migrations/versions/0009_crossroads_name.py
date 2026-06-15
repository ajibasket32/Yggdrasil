"""Align canonical crossroads location display name with test contract.

Revision ID: 0009_crossroads_name
Revises: 0008_greenwood_name
Create Date: 2026-06-15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009_crossroads_name"
down_revision: str | None = "0008_greenwood_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Use the canonical service-facing crossroads name."""
    op.execute("""
        UPDATE locations
        SET name = 'Ancient Crossroads'
        WHERE id = '56000000-0000-0000-0000-000000000004'
        """)


def downgrade() -> None:
    """Restore the previous seed name on rollback."""
    op.execute("""
        UPDATE locations
        SET name = 'Ancient Valerian Crossroads'
        WHERE id = '56000000-0000-0000-0000-000000000004'
        """)
