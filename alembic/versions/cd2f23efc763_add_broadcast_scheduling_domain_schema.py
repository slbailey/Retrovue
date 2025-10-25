"""Add broadcast scheduling domain schema

Revision ID: cd2f23efc763
Revises: 5765675cf5d3
Create Date: 2025-01-24 20:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cd2f23efc763'
down_revision: Union[str, Sequence[str], None] = '5765675cf5d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    This migration introduces the broadcast scheduling domain schema.
    
    - `channel` defines channel timing policy.
    - `template` / `template_block` define daypart programming rules.
    - `schedule_day` assigns a template to a channel+broadcast day.
    - `catalog_asset` is the broadcast-approved catalog.
    - `playlog_event` is where ScheduleService will write generated playout.
    """
    
    # Create broadcast_channel table
    op.create_table('broadcast_channel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('timezone', sa.Text(), nullable=False),  # IANA tz string
        sa.Column('grid_size_minutes', sa.Integer(), nullable=False),
        sa.Column('grid_offset_minutes', sa.Integer(), nullable=False),
        sa.Column('rollover_minutes', sa.Integer(), nullable=False),  # minutes after local midnight, e.g. 360 for 06:00
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
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
        sa.Column('start_time', sa.Text(), nullable=False),  # "HH:MM" local wallclock
        sa.Column('end_time', sa.Text(), nullable=False),    # "HH:MM"
        sa.Column('rule_json', sa.Text(), nullable=False),   # e.g. {"tags":["sitcom"], "episode_policy":"syndication"}
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['template_id'], ['broadcast_template.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_broadcast_template_block_template_id', 'broadcast_template_block', ['template_id'])
    
    # Create broadcast_schedule_day table
    op.create_table('broadcast_schedule_day',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('schedule_date', sa.Text(), nullable=False),  # "YYYY-MM-DD" broadcast-day label, 06:00→06:00 policy
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['channel_id'], ['broadcast_channel.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['broadcast_template.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('channel_id', 'schedule_date', name='uq_broadcast_schedule_day_channel_date')
    )
    op.create_index('ix_broadcast_schedule_day_channel_id', 'broadcast_schedule_day', ['channel_id'])
    
    # Create catalog_asset table
    op.create_table('catalog_asset',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('tags', sa.Text(), nullable=True),  # comma-separated tags like "sitcom,retro"
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('canonical', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_catalog_asset_canonical', 'catalog_asset', ['canonical'])
    op.create_index('ix_catalog_asset_tags', 'catalog_asset', ['tags'])
    
    # Create broadcast_playlog_event table
    op.create_table('broadcast_playlog_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('start_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('broadcast_day', sa.Text(), nullable=False),  # "YYYY-MM-DD" broadcast day label
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['channel_id'], ['broadcast_channel.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['catalog_asset.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_broadcast_playlog_event_channel_id', 'broadcast_playlog_event', ['channel_id'])
    op.create_index('ix_broadcast_playlog_event_channel_start', 'broadcast_playlog_event', ['channel_id', 'start_utc'])
    op.create_index('ix_broadcast_playlog_event_broadcast_day', 'broadcast_playlog_event', ['broadcast_day'])


def downgrade() -> None:
    """Downgrade schema."""
    
    # Drop tables in reverse dependency order
    op.drop_index('ix_broadcast_playlog_event_broadcast_day', table_name='broadcast_playlog_event')
    op.drop_index('ix_broadcast_playlog_event_channel_start', table_name='broadcast_playlog_event')
    op.drop_index('ix_broadcast_playlog_event_channel_id', table_name='broadcast_playlog_event')
    op.drop_table('broadcast_playlog_event')
    
    op.drop_index('ix_catalog_asset_tags', table_name='catalog_asset')
    op.drop_index('ix_catalog_asset_canonical', table_name='catalog_asset')
    op.drop_table('catalog_asset')
    
    op.drop_index('ix_broadcast_schedule_day_channel_id', table_name='broadcast_schedule_day')
    op.drop_table('broadcast_schedule_day')
    
    op.drop_index('ix_broadcast_template_block_template_id', table_name='broadcast_template_block')
    op.drop_table('broadcast_template_block')
    
    op.drop_table('broadcast_template')
    op.drop_table('broadcast_channel')