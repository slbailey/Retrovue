"""create_assets_table

Revision ID: a5c7b3f0c1d2
Revises: 9541bbc23bcd
Create Date: 2025-10-29 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a5c7b3f0c1d2"
down_revision: Union[str, Sequence[str], None] = "a5c7b3f0c1d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type for asset_state
    asset_state = sa.Enum("new", "enriching", "ready", "retired", name="asset_state")
    asset_state.create(op.get_bind(), checkfirst=True)

    # Create assets table (final schema)
    op.create_table(
        "assets",
        sa.Column("uuid", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("collection_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_key", sa.Text(), nullable=False),
        sa.Column("canonical_key_hash", sa.String(length=64), nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("state", asset_state, nullable=False),
        sa.Column("approved_for_broadcast", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("operator_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("video_codec", sa.String(length=50), nullable=True),
        sa.Column("audio_codec", sa.String(length=50), nullable=True),
        sa.Column("container", sa.String(length=50), nullable=True),
        sa.Column("hash_sha256", sa.String(length=64), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_enricher_checksum", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["collection_uuid"], ["collections.uuid"], name="assets_collection_uuid_fkey", ondelete="RESTRICT"),
        sa.UniqueConstraint("collection_uuid", "canonical_key_hash", name="ix_assets_collection_canonical_unique"),
        sa.UniqueConstraint("collection_uuid", "uri", name="ix_assets_collection_uri_unique"),
        sa.CheckConstraint("(NOT approved_for_broadcast) OR (state = 'ready')", name="chk_approved_implies_ready"),
        sa.CheckConstraint("(is_deleted = TRUE AND deleted_at IS NOT NULL) OR (is_deleted = FALSE AND deleted_at IS NULL)", name="chk_deleted_at_sync"),
        sa.CheckConstraint("char_length(canonical_key_hash) = 64", name="chk_canon_hash_len"),
        sa.CheckConstraint("canonical_key_hash ~ '^[0-9a-f]{64}$'", name="chk_canon_hash_hex"),
    )

    # Standard indexes
    op.create_index("ix_assets_collection_uuid", "assets", ["collection_uuid"], unique=False)
    op.create_index("ix_assets_state", "assets", ["state"], unique=False)
    op.create_index("ix_assets_approved", "assets", ["approved_for_broadcast"], unique=False)
    op.create_index("ix_assets_operator_verified", "assets", ["operator_verified"], unique=False)
    op.create_index("ix_assets_discovered_at", "assets", ["discovered_at"], unique=False)
    op.create_index("ix_assets_is_deleted", "assets", ["is_deleted"], unique=False)

    # Partial schedulable index (hot path)
    op.create_index(
        "ix_assets_schedulable",
        "assets",
        ["collection_uuid", "discovered_at"],
        unique=False,
        postgresql_where=sa.text("state = 'ready' AND approved_for_broadcast = true AND is_deleted = false"),
    )

    # updated_at trigger function
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION set_updated_at()
            RETURNS trigger AS $$
            BEGIN
              NEW.updated_at = NOW();
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )

    # updated_at trigger
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_assets_set_updated_at ON assets;
            CREATE TRIGGER trg_assets_set_updated_at
            BEFORE UPDATE ON assets
            FOR EACH ROW
            EXECUTE FUNCTION set_updated_at();
            """
        )
    )


def downgrade() -> None:
    # Drop trigger and function
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_assets_set_updated_at ON assets;"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS set_updated_at();"))

    # Drop indexes
    op.drop_index("ix_assets_schedulable", table_name="assets")
    op.drop_index("ix_assets_is_deleted", table_name="assets")
    op.drop_index("ix_assets_discovered_at", table_name="assets")
    op.drop_index("ix_assets_operator_verified", table_name="assets")
    op.drop_index("ix_assets_approved", table_name="assets")
    op.drop_index("ix_assets_state", table_name="assets")
    op.drop_index("ix_assets_collection_uuid", table_name="assets")

    # Drop table
    op.drop_table("assets")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS asset_state")


