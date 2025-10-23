"""add_soft_delete_to_assets

Revision ID: 6965919427dd
Revises: a0f57a8b7188
Create Date: 2025-10-23 10:10:12.777125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6965919427dd'
down_revision: Union[str, Sequence[str], None] = 'a0f57a8b7188'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add soft delete columns to assets table
    op.add_column('assets', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('assets', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add index for soft delete queries
    op.create_index('ix_assets_is_deleted', 'assets', ['is_deleted'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove soft delete columns
    op.drop_index('ix_assets_is_deleted', table_name='assets')
    op.drop_column('assets', 'deleted_at')
    op.drop_column('assets', 'is_deleted')
