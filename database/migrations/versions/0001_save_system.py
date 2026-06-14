"""Create versioned transactional save storage.

Revision ID: 0001_save_system
Revises:
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_save_system"
down_revision: str | None = None
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
    """Create save and idempotency tables with database-managed audit fields."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """)

    op.create_table(
        "save_games",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("save_name", sa.String(length=120), nullable=False),
        sa.Column("save_version", sa.Integer(), nullable=False),
        sa.Column("world_tick", sa.BigInteger(), nullable=False),
        sa.Column(
            "snapshot_reference",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("snapshot_checksum", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("world_tick >= 0", name="ck_save_games_world_tick"),
        sa.CheckConstraint("schema_version >= 0", name="ck_save_games_schema_version"),
        sa.CheckConstraint(
            "status IN ('VERIFIED', 'UNVERIFIED', 'CORRUPT')",
            name="ck_save_games_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "player_id",
            "character_id",
            "save_version",
            name="uq_save_games_character_version",
        ),
    )
    op.create_index("ix_save_games_player_id", "save_games", ["player_id"])
    op.create_index("ix_save_games_character_id", "save_games", ["character_id"])
    op.create_index(
        "ix_save_games_active_player",
        "save_games",
        ["player_id", "deleted_at"],
    )

    op.create_table(
        "idempotency_records",
        *_audit_columns(),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=80), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column(
            "response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "player_id",
            "idempotency_key",
            "operation",
            name="uq_idempotency_actor_key_operation",
        ),
    )
    op.create_index(
        "ix_idempotency_records_expires_at",
        "idempotency_records",
        ["expires_at"],
    )

    for table in ("save_games", "idempotency_records"):
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """)


def downgrade() -> None:
    """Remove v0.2 persistence structures without touching unrelated data."""
    op.drop_table("idempotency_records")
    op.drop_table("save_games")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")
