"""Align the combat transactional outbox with the canonical event contract.

Revision ID: 0005_combat_outbox_contract
Revises: 0004_combat_system
Create Date: 2026-06-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_combat_outbox_contract"
down_revision: str | None = "0004_combat_system"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Promote the release-local outbox to the canonical shared contract."""
    op.rename_table("game_outbox_events", "outbox_events")
    op.execute(
        "ALTER INDEX ix_game_outbox_events_event_type "
        "RENAME TO ix_outbox_events_event_type"
    )
    op.execute(
        "ALTER TABLE outbox_events "
        "RENAME CONSTRAINT uq_game_outbox_deduplication "
        "TO uq_outbox_deduplication"
    )
    op.execute(
        "ALTER TRIGGER trg_game_outbox_events_updated_at ON outbox_events "
        "RENAME TO trg_outbox_events_updated_at"
    )
    op.add_column(
        "outbox_events",
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.add_column(
        "outbox_events",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "outbox_events",
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_outbox_events_aggregate_id",
        "outbox_events",
        ["aggregate_id"],
    )
    op.create_index(
        "ix_outbox_events_published_at",
        "outbox_events",
        ["published_at"],
    )


def downgrade() -> None:
    """Restore the initial v0.6 release-local outbox representation."""
    op.drop_index("ix_outbox_events_published_at", table_name="outbox_events")
    op.drop_index("ix_outbox_events_aggregate_id", table_name="outbox_events")
    op.drop_column("outbox_events", "last_error")
    op.drop_column("outbox_events", "attempt_count")
    op.drop_column("outbox_events", "occurred_at")
    op.execute(
        "ALTER TRIGGER trg_outbox_events_updated_at ON outbox_events "
        "RENAME TO trg_game_outbox_events_updated_at"
    )
    op.execute(
        "ALTER TABLE outbox_events "
        "RENAME CONSTRAINT uq_outbox_deduplication "
        "TO uq_game_outbox_deduplication"
    )
    op.execute(
        "ALTER INDEX ix_outbox_events_event_type "
        "RENAME TO ix_game_outbox_events_event_type"
    )
    op.rename_table("outbox_events", "game_outbox_events")
