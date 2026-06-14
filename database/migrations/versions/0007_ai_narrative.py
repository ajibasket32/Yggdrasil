"""Store validated cosmetic narrative outside canonical gameplay state.

Revision ID: 0007_ai_narrative
Revises: 0006_world_npc_quest
Create Date: 2026-06-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_ai_narrative"
down_revision: str | None = "0006_world_npc_quest"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the audited v0.8 narrative history."""
    op.create_table(
        "narrative_records",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("npc_id", sa.Uuid(), sa.ForeignKey("npcs.id"), nullable=True),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("topic_id", sa.String(40), nullable=False),
        sa.Column("request_key", sa.String(200), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("prompt_version", sa.String(40), nullable=False),
        sa.Column("context_hash", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(40), nullable=False),
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "referenced_entity_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "fallback_used", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("cached", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "player_id",
            "kind",
            "request_key",
            name="uq_narrative_records_request",
        ),
    )
    for column in ("player_id", "character_id", "npc_id", "entity_id", "kind"):
        op.create_index(
            f"ix_narrative_records_{column}", "narrative_records", [column]
        )
    op.create_index(
        "ix_narrative_records_context",
        "narrative_records",
        [
            "player_id",
            "character_id",
            "kind",
            "entity_id",
            "context_hash",
            "prompt_version",
        ],
    )
    op.execute("""
        CREATE TRIGGER trg_narrative_records_updated_at
        BEFORE UPDATE ON narrative_records
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """)


def downgrade() -> None:
    """Remove cosmetic narrative history without touching gameplay state."""
    op.drop_table("narrative_records")
