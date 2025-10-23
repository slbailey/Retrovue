"""fix_assets_identity_model

Revision ID: 5765675cf5d3
Revises: 6965919427dd
Create Date: 2025-10-23 10:14:57.507908

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5765675cf5d3'
down_revision: Union[str, Sequence[str], None] = '6965919427dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Add new integer id column with AUTOINCREMENT
    op.add_column('assets', sa.Column('id_new', sa.Integer(), nullable=False, server_default='0'))
    
    # Step 2: Populate id_new with sequential values based on row order
    # This ensures proper ordering for the new integer primary key
    op.execute("""
        WITH numbered_assets AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY discovered_at, id) as new_id
            FROM assets
        )
        UPDATE assets 
        SET id_new = numbered_assets.new_id
        FROM numbered_assets
        WHERE assets.id = numbered_assets.id
    """)
    
    # Step 3: Update all foreign key tables to reference the new integer id
    # Update episode_assets table
    op.add_column('episode_assets', sa.Column('asset_id_new', sa.Integer(), nullable=True))
    op.execute("""
        UPDATE episode_assets 
        SET asset_id_new = (
            SELECT a.id_new 
            FROM assets a 
            WHERE a.id = episode_assets.asset_id
        )
    """)
    # Drop constraint if it exists
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
                      WHERE constraint_name = 'episode_assets_asset_id_fkey' 
                      AND table_name = 'episode_assets') THEN
                ALTER TABLE episode_assets DROP CONSTRAINT episode_assets_asset_id_fkey;
            END IF;
        END $$;
    """)
    op.drop_column('episode_assets', 'asset_id')
    op.alter_column('episode_assets', 'asset_id_new', new_column_name='asset_id', nullable=False)
    # Foreign key will be created after we rename id_new to id
    
    # Update provider_refs table
    op.add_column('provider_refs', sa.Column('asset_id_new', sa.Integer(), nullable=True))
    op.execute("""
        UPDATE provider_refs 
        SET asset_id_new = (
            SELECT a.id_new 
            FROM assets a 
            WHERE a.id = provider_refs.asset_id
        )
    """)
    # Drop constraint if it exists
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
                      WHERE constraint_name = 'provider_refs_asset_id_fkey' 
                      AND table_name = 'provider_refs') THEN
                ALTER TABLE provider_refs DROP CONSTRAINT provider_refs_asset_id_fkey;
            END IF;
        END $$;
    """)
    op.drop_column('provider_refs', 'asset_id')
    op.alter_column('provider_refs', 'asset_id_new', new_column_name='asset_id', nullable=True)
    # Foreign key will be created after we rename id_new to id
    
    # Update markers table
    op.add_column('markers', sa.Column('asset_id_new', sa.Integer(), nullable=True))
    op.execute("""
        UPDATE markers 
        SET asset_id_new = (
            SELECT a.id_new 
            FROM assets a 
            WHERE a.id = markers.asset_id
        )
    """)
    # Drop constraint if it exists
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
                      WHERE constraint_name = 'markers_asset_id_fkey' 
                      AND table_name = 'markers') THEN
                ALTER TABLE markers DROP CONSTRAINT markers_asset_id_fkey;
            END IF;
        END $$;
    """)
    op.drop_column('markers', 'asset_id')
    op.alter_column('markers', 'asset_id_new', new_column_name='asset_id', nullable=False)
    # Foreign key will be created after we rename id_new to id
    
    # Update review_queue table
    op.add_column('review_queue', sa.Column('asset_id_new', sa.Integer(), nullable=True))
    op.execute("""
        UPDATE review_queue 
        SET asset_id_new = (
            SELECT a.id_new 
            FROM assets a 
            WHERE a.id = review_queue.asset_id
        )
    """)
    # Drop constraint if it exists
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
                      WHERE constraint_name = 'review_queue_asset_id_fkey' 
                      AND table_name = 'review_queue') THEN
                ALTER TABLE review_queue DROP CONSTRAINT review_queue_asset_id_fkey;
            END IF;
        END $$;
    """)
    op.drop_column('review_queue', 'asset_id')
    op.alter_column('review_queue', 'asset_id_new', new_column_name='asset_id', nullable=False)
    # Foreign key will be created after we rename id_new to id
    
    # Step 4: Drop the old primary key constraint and rename columns
    # Drop primary key constraint if it exists
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
                      WHERE constraint_name = 'assets_pkey' 
                      AND table_name = 'assets' 
                      AND constraint_type = 'PRIMARY KEY') THEN
                ALTER TABLE assets DROP CONSTRAINT assets_pkey;
            END IF;
        END $$;
    """)
    op.drop_column('assets', 'id')
    op.alter_column('assets', 'id_new', new_column_name='id')
    op.create_primary_key('assets_pkey', 'assets', ['id'])
    
    # Step 5: Ensure uuid column is properly configured
    # Make sure uuid is unique and not null
    op.alter_column('assets', 'uuid', nullable=False)
    op.create_unique_constraint('assets_uuid_key', 'assets', ['uuid'])
    
    # Step 6: Create foreign key constraints now that id is the primary key
    op.create_foreign_key('episode_assets_asset_id_fkey', 'episode_assets', 'assets', ['asset_id'], ['id'])
    op.create_foreign_key('provider_refs_asset_id_fkey', 'provider_refs', 'assets', ['asset_id'], ['id'])
    op.create_foreign_key('markers_asset_id_fkey', 'markers', 'assets', ['asset_id'], ['id'])
    op.create_foreign_key('review_queue_asset_id_fkey', 'review_queue', 'assets', ['asset_id'], ['id'])
    
    # Step 7: Create required indexes
    op.create_index('assets_uuid_idx', 'assets', ['uuid'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # This is a complex migration that changes primary key types
    # Downgrade would require recreating all UUID foreign keys
    # For safety, we'll raise an exception to prevent accidental downgrade
    raise Exception("This migration cannot be safely downgraded due to primary key type changes")
