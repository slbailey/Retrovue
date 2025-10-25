"""initial base schema

Revision ID: 0001_initial_base_schema
Revises: 
Create Date: 2025-01-24 20:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_base_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the complete base schema for Retrovue."""
    
    # Create enums first (only if they don't exist)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE titlekind AS ENUM ('MOVIE', 'SHOW');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE markerkind AS ENUM ('CHAPTER', 'AVAIL', 'BUMPER', 'INTRO', 'OUTRO');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reviewstatus AS ENUM ('PENDING', 'RESOLVED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE entitytype AS ENUM ('TITLE', 'EPISODE', 'ASSET');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE provider AS ENUM ('PLEX', 'JELLYFIN', 'FILESYSTEM', 'MANUAL');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create titles table
    op.create_table('titles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('kind', postgresql.ENUM('MOVIE', 'SHOW', name='titlekind', create_type=False), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('external_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create seasons table
    op.create_table('seasons',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title_id', sa.UUID(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['title_id'], ['titles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create episodes table
    op.create_table('episodes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title_id', sa.UUID(), nullable=False),
        sa.Column('season_id', sa.UUID(), nullable=True),
        sa.Column('number', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('external_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['title_id'], ['titles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create assets table (with integer primary key and UUID)
    op.create_table('assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('uri', sa.Text(), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('video_codec', sa.String(length=50), nullable=True),
        sa.Column('audio_codec', sa.String(length=50), nullable=True),
        sa.Column('container', sa.String(length=50), nullable=True),
        sa.Column('hash_sha256', sa.String(length=64), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('canonical', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('uri')
    )
    
    # Create episode_assets junction table
    op.create_table('episode_assets',
        sa.Column('episode_id', sa.UUID(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('episode_id', 'asset_id')
    )
    
    # Create provider_refs table
    op.create_table('provider_refs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('entity_type', postgresql.ENUM('TITLE', 'EPISODE', 'ASSET', name='entitytype', create_type=False), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('provider', postgresql.ENUM('PLEX', 'JELLYFIN', 'FILESYSTEM', 'MANUAL', name='provider', create_type=False), nullable=False),
        sa.Column('provider_key', sa.Text(), nullable=False),
        sa.Column('raw', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('title_id', sa.UUID(), nullable=True),
        sa.Column('episode_id', sa.UUID(), nullable=True),
        sa.Column('asset_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['title_id'], ['titles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create markers table
    op.create_table('markers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('kind', postgresql.ENUM('CHAPTER', 'AVAIL', 'BUMPER', 'INTRO', 'OUTRO', name='markerkind', create_type=False), nullable=False),
        sa.Column('start_ms', sa.Integer(), nullable=False),
        sa.Column('end_ms', sa.Integer(), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create review_queue table
    op.create_table('review_queue',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'RESOLVED', name='reviewstatus', create_type=False), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create sources table
    op.create_table('sources',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('kind', sa.String(length=50), nullable=False),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id')
    )
    
    # Create source_collections table
    op.create_table('source_collections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_id', 'external_id', name='uq_source_collections_source_external')
    )
    
    # Create path_mappings table
    op.create_table('path_mappings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('collection_id', sa.UUID(), nullable=False),
        sa.Column('plex_path', sa.String(length=500), nullable=False),
        sa.Column('local_path', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['source_collections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create broadcast_channel table
    op.create_table('broadcast_channel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('timezone', sa.Text(), nullable=False),
        sa.Column('grid_size_minutes', sa.Integer(), nullable=False),
        sa.Column('grid_offset_minutes', sa.Integer(), nullable=False),
        sa.Column('rollover_minutes', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('uuid')
    )
    
    # Create broadcast_template table
    op.create_table('broadcast_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create broadcast_template_block table
    op.create_table('broadcast_template_block',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Text(), nullable=False),
        sa.Column('end_time', sa.Text(), nullable=False),
        sa.Column('rule_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['template_id'], ['broadcast_template.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create broadcast_schedule_day table
    op.create_table('broadcast_schedule_day',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('schedule_date', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['channel_id'], ['broadcast_channel.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['broadcast_template.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('channel_id', 'schedule_date', name='uq_broadcast_schedule_day_channel_date')
    )
    
    # Create catalog_asset table
    op.create_table('catalog_asset',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('canonical', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('source_ingest_asset_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['source_ingest_asset_id'], ['assets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # Create broadcast_playlog_event table
    op.create_table('broadcast_playlog_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('start_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('broadcast_day', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['channel_id'], ['broadcast_channel.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['catalog_asset.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # Create indexes for assets table
    op.create_index('ix_assets_canonical', 'assets', ['canonical'])
    op.create_index('ix_assets_discovered_at', 'assets', ['discovered_at'])
    op.create_index('ix_assets_is_deleted', 'assets', ['is_deleted'])
    
    # Create indexes for markers table
    op.create_index('ix_markers_asset_id', 'markers', ['asset_id'])
    op.create_index('ix_markers_kind', 'markers', ['kind'])
    
    # Create indexes for review_queue table
    op.create_index('ix_review_queue_asset_id', 'review_queue', ['asset_id'])
    op.create_index('ix_review_queue_status', 'review_queue', ['status'])
    op.create_index('ix_review_queue_created_at', 'review_queue', ['created_at'])
    
    # Create indexes for source_collections table
    op.create_index('ix_source_collections_source_id', 'source_collections', ['source_id'])
    op.create_index('ix_source_collections_enabled', 'source_collections', ['enabled'])
    
    # Create indexes for path_mappings table
    op.create_index('ix_path_mappings_collection_id', 'path_mappings', ['collection_id'])
    
    # Create indexes for broadcast_template_block table
    op.create_index('ix_broadcast_template_block_template_id', 'broadcast_template_block', ['template_id'])
    
    # Create indexes for broadcast_schedule_day table
    op.create_index('ix_broadcast_schedule_day_channel_id', 'broadcast_schedule_day', ['channel_id'])
    
    # Create indexes for catalog_asset table
    op.create_index('ix_catalog_asset_canonical', 'catalog_asset', ['canonical'])
    op.create_index('ix_catalog_asset_tags', 'catalog_asset', ['tags'])
    op.create_index('ix_catalog_asset_source_ingest_asset_id', 'catalog_asset', ['source_ingest_asset_id'])
    
    # Create indexes for broadcast_playlog_event table
    op.create_index('ix_broadcast_playlog_event_channel_id', 'broadcast_playlog_event', ['channel_id'])
    op.create_index('ix_broadcast_playlog_event_channel_start', 'broadcast_playlog_event', ['channel_id', 'start_utc'])
    op.create_index('ix_broadcast_playlog_event_broadcast_day', 'broadcast_playlog_event', ['broadcast_day'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse dependency order
    op.drop_table('broadcast_playlog_event')
    op.drop_table('catalog_asset')
    op.drop_table('broadcast_schedule_day')
    op.drop_table('broadcast_template_block')
    op.drop_table('broadcast_template')
    op.drop_table('broadcast_channel')
    op.drop_table('path_mappings')
    op.drop_table('source_collections')
    op.drop_table('sources')
    op.drop_table('review_queue')
    op.drop_table('markers')
    op.drop_table('provider_refs')
    op.drop_table('episode_assets')
    op.drop_table('assets')
    op.drop_table('episodes')
    op.drop_table('seasons')
    op.drop_table('titles')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS provider")
    op.execute("DROP TYPE IF EXISTS entitytype")
    op.execute("DROP TYPE IF EXISTS reviewstatus")
    op.execute("DROP TYPE IF EXISTS markerkind")
    op.execute("DROP TYPE IF EXISTS titlekind")
