"""add_collection_id_to_assets

Revision ID: 753624484d37
Revises: 6643d387b40e
Create Date: 2025-10-26 07:05:07.267533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '753624484d37'
down_revision: Union[str, Sequence[str], None] = '6643d387b40e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add collection_id column to assets table
    op.add_column('assets', sa.Column('collection_id', sa.UUID(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_assets_collection_id',
        'assets', 'source_collections',
        ['collection_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for performance
    op.create_index('ix_assets_collection_id', 'assets', ['collection_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove index
    op.drop_index('ix_assets_collection_id', 'assets')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_assets_collection_id', 'assets', type_='foreignkey')
    
    # Remove column
    op.drop_column('assets', 'collection_id')
