"""Create canonical memory and retryable vector-index job storage.

Revision ID: 0002_rag_memory
Revises: 0001_save_system
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_rag_memory"
down_revision: str | None = "0001_save_system"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _audit_columns() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
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
    ]


def upgrade() -> None:
    """Create canonical memory, link, and index-job tables."""
    op.create_table(
        "memories",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("memory_type", sa.String(length=40), nullable=False),
        sa.Column("source_entity_type", sa.String(length=40), nullable=False),
        sa.Column("source_entity_id", sa.Uuid(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("importance", sa.SmallInteger(), nullable=False),
        sa.Column("world_event_id", sa.Uuid(), nullable=True),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column(
            "participants",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("location_id", sa.Uuid(), nullable=True),
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column(
            "index_status",
            sa.String(length=20),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "importance BETWEEN 1 AND 10",
            name="ck_memories_importance",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'DELETED')",
            name="ck_memories_status",
        ),
        sa.CheckConstraint(
            "index_status IN ('PENDING', 'INDEXED', 'FAILED', 'DELETED')",
            name="ck_memories_index_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memories_player_id", "memories", ["player_id"])
    op.create_index("ix_memories_memory_type", "memories", ["memory_type"])
    op.create_index("ix_memories_world_event_id", "memories", ["world_event_id"])
    op.create_index("ix_memories_entity_id", "memories", ["entity_id"])
    op.create_index("ix_memories_location_id", "memories", ["location_id"])
    op.create_index("ix_memories_occurred_at", "memories", ["occurred_at"])
    op.create_index(
        "uq_memories_active_content",
        "memories",
        [
            "player_id",
            "memory_type",
            "entity_type",
            "entity_id",
            "content_hash",
        ],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "memory_links",
        *_audit_columns(),
        sa.Column(
            "memory_a_id",
            sa.Uuid(),
            sa.ForeignKey("memories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "memory_b_id",
            sa.Uuid(),
            sa.ForeignKey("memories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(length=40), nullable=False),
        sa.CheckConstraint(
            "memory_a_id <> memory_b_id",
            name="ck_memory_links_distinct_memories",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "memory_a_id",
            "memory_b_id",
            "relationship_type",
            name="uq_memory_links_relationship",
        ),
    )
    op.create_index("ix_memory_links_memory_a_id", "memory_links", ["memory_a_id"])
    op.create_index("ix_memory_links_memory_b_id", "memory_links", ["memory_b_id"])

    op.create_table(
        "memory_index_jobs",
        *_audit_columns(),
        sa.Column(
            "memory_id",
            sa.Uuid(),
            sa.ForeignKey("memories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("operation", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error_code", sa.String(length=80), nullable=True),
        sa.CheckConstraint(
            "operation IN ('UPSERT', 'DELETE')",
            name="ck_memory_index_jobs_operation",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'RETRY', 'COMPLETED', 'FAILED')",
            name="ck_memory_index_jobs_status",
        ),
        sa.CheckConstraint(
            "attempts >= 0 AND max_attempts > 0",
            name="ck_memory_index_jobs_attempts",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_memory_index_jobs_memory_id",
        "memory_index_jobs",
        ["memory_id"],
    )
    op.create_index(
        "ix_memory_index_jobs_next_attempt_at",
        "memory_index_jobs",
        ["next_attempt_at"],
    )
    op.create_index(
        "ix_memory_index_jobs_due",
        "memory_index_jobs",
        ["status", "next_attempt_at"],
    )

    for table in ("memories", "memory_links", "memory_index_jobs"):
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """)


def downgrade() -> None:
    """Remove v0.4 memory structures without changing save data."""
    op.drop_table("memory_index_jobs")
    op.drop_table("memory_links")
    op.drop_table("memories")
