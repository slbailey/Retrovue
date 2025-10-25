"""rename_broadcast_channel_to_broadcast_channels

Revision ID: 6643d387b40e
Revises: 0001_initial_base_schema
Create Date: 2025-10-25 11:46:37.890512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6643d387b40e'
down_revision: Union[str, Sequence[str], None] = '0001_initial_base_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename broadcast_channel to broadcast_channels and add updated_at column."""
    # Rename the table
    op.rename_table('broadcast_channel', 'broadcast_channels')
    
    # Add updated_at column
    op.add_column('broadcast_channels', 
                  sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove updated_at column
    op.drop_column('broadcast_channels', 'updated_at')
    
    # Rename the table back
    op.rename_table('broadcast_channels', 'broadcast_channel')
