"""remove_obsolete_scheduling_tables_from_library_domain

Revision ID: 68fecbe0ea79
Revises: cd2f23efc763
Create Date: 2025-10-24 20:37:43.268395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '68fecbe0ea79'
down_revision: Union[str, Sequence[str], None] = 'cd2f23efc763'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    This migration removes obsolete scheduling tables from the Library Domain. The
    Broadcast Domain (singular table names) is now authoritative for channel policy,
    scheduling, broadcast catalog, and playlog_event. The Library Domain is now
    responsible ONLY for content ingestion, metadata, QC, and promotion into the
    broadcast catalog.
    """
    
    # Drop obsolete scheduling tables from Library Domain
    # Use IF EXISTS to handle cases where tables may not exist
    op.execute("DROP TABLE IF EXISTS channels CASCADE")
    op.execute("DROP TABLE IF EXISTS templates CASCADE") 
    op.execute("DROP TABLE IF EXISTS template_blocks CASCADE")
    op.execute("DROP TABLE IF EXISTS schedule_days CASCADE")
    op.execute("DROP TABLE IF EXISTS playlog_events CASCADE")


def downgrade() -> None:
    """Downgrade schema - recreate legacy scheduling tables (best effort)."""
    
    # Recreate legacy scheduling tables with minimal columns
    # Note: These are marked as legacy and may not have full functionality
    
    # Create channels table (legacy)
    op.create_table('channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('timezone', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create templates table (legacy)
    op.create_table('templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create template_blocks table (legacy)
    op.create_table('template_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Text(), nullable=False),
        sa.Column('end_time', sa.Text(), nullable=False),
        sa.Column('rule_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create schedule_days table (legacy)
    op.create_table('schedule_days',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('schedule_date', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create playlog_events table (legacy)
    op.create_table('playlog_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('start_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('broadcast_day', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
