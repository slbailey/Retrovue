"""reconcile_schema_with_identity_rules

Revision ID: bf8944bf48c4
Revises: af4b0859d475
Create Date: 2025-10-25 10:12:29.265197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'bf8944bf48c4'
down_revision: Union[str, Sequence[str], None] = 'af4b0859d475'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Reconcile database schema with current SQLAlchemy models according to identity rules.
    
    Changes:
    1. Add UUID columns to broadcast_channel and broadcast_playlog_event tables
    2. Add foreign key constraint for catalog_asset.source_ingest_asset_id → assets.id
    3. Add missing indexes for performance
    4. Ensure all tables follow the id (INTEGER PK) + uuid (stable external identity) pattern
    """
    
    # Add UUID column to broadcast_channel table
    op.add_column('broadcast_channel', sa.Column('uuid', UUID(as_uuid=True), nullable=True))
    
    # Populate UUID values for existing records
    op.execute("""
        UPDATE broadcast_channel 
        SET uuid = gen_random_uuid() 
        WHERE uuid IS NULL
    """)
    
    # Make UUID column non-nullable and unique
    op.alter_column('broadcast_channel', 'uuid', nullable=False)
    op.create_unique_constraint('uq_broadcast_channel_uuid', 'broadcast_channel', ['uuid'])
    op.create_index('ix_broadcast_channel_uuid', 'broadcast_channel', ['uuid'], unique=True)
    
    # Add UUID column to catalog_asset table
    op.add_column('catalog_asset', sa.Column('uuid', UUID(as_uuid=True), nullable=True))
    
    # Populate UUID values for existing records
    op.execute("""
        UPDATE catalog_asset 
        SET uuid = gen_random_uuid() 
        WHERE uuid IS NULL
    """)
    
    # Make UUID column non-nullable and unique
    op.alter_column('catalog_asset', 'uuid', nullable=False)
    op.create_unique_constraint('uq_catalog_asset_uuid', 'catalog_asset', ['uuid'])
    op.create_index('ix_catalog_asset_uuid', 'catalog_asset', ['uuid'], unique=True)
    
    # Add UUID column to broadcast_playlog_event table
    op.add_column('broadcast_playlog_event', sa.Column('uuid', UUID(as_uuid=True), nullable=True))
    
    # Populate UUID values for existing records
    op.execute("""
        UPDATE broadcast_playlog_event 
        SET uuid = gen_random_uuid() 
        WHERE uuid IS NULL
    """)
    
    # Make UUID column non-nullable and unique
    op.alter_column('broadcast_playlog_event', 'uuid', nullable=False)
    op.create_unique_constraint('uq_broadcast_playlog_event_uuid', 'broadcast_playlog_event', ['uuid'])
    op.create_index('ix_broadcast_playlog_event_uuid', 'broadcast_playlog_event', ['uuid'], unique=True)
    
    # Add foreign key constraint for catalog_asset.source_ingest_asset_id → assets.id
    # First check if the constraint doesn't already exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                          WHERE constraint_name = 'fk_catalog_asset_source_ingest_asset_id_assets' 
                          AND table_name = 'catalog_asset') THEN
                ALTER TABLE catalog_asset 
                ADD CONSTRAINT fk_catalog_asset_source_ingest_asset_id_assets 
                FOREIGN KEY (source_ingest_asset_id) REFERENCES assets(id) ON DELETE SET NULL;
            END IF;
        END $$;
    """)
    
    # Add index for source_ingest_asset_id if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes 
                          WHERE indexname = 'ix_catalog_asset_source_ingest_asset_id' 
                          AND tablename = 'catalog_asset') THEN
                CREATE INDEX ix_catalog_asset_source_ingest_asset_id ON catalog_asset(source_ingest_asset_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """
    Downgrade schema changes.
    """
    
    # Drop indexes and constraints for UUID columns
    op.drop_index('ix_broadcast_playlog_event_uuid', table_name='broadcast_playlog_event')
    op.drop_constraint('uq_broadcast_playlog_event_uuid', 'broadcast_playlog_event', type_='unique')
    op.drop_column('broadcast_playlog_event', 'uuid')
    
    op.drop_index('ix_catalog_asset_uuid', table_name='catalog_asset')
    op.drop_constraint('uq_catalog_asset_uuid', 'catalog_asset', type_='unique')
    op.drop_column('catalog_asset', 'uuid')
    
    op.drop_index('ix_broadcast_channel_uuid', table_name='broadcast_channel')
    op.drop_constraint('uq_broadcast_channel_uuid', 'broadcast_channel', type_='unique')
    op.drop_column('broadcast_channel', 'uuid')
    
    # Drop foreign key constraint and index for source_ingest_asset_id
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
                      WHERE constraint_name = 'fk_catalog_asset_source_ingest_asset_id_assets' 
                      AND table_name = 'catalog_asset') THEN
                ALTER TABLE catalog_asset DROP CONSTRAINT fk_catalog_asset_source_ingest_asset_id_assets;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_indexes 
                      WHERE indexname = 'ix_catalog_asset_source_ingest_asset_id' 
                      AND tablename = 'catalog_asset') THEN
                DROP INDEX ix_catalog_asset_source_ingest_asset_id;
            END IF;
        END $$;
    """)
