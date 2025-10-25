"""add_source_ingest_asset_id_to_catalog_asset

Revision ID: af4b0859d475
Revises: 68fecbe0ea79
Create Date: 2025-10-24 20:40:15.547609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af4b0859d475'
down_revision: Union[str, Sequence[str], None] = '68fecbe0ea79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add source_ingest_asset_id field to catalog_asset table for traceability."""
    op.add_column('catalog_asset', sa.Column('source_ingest_asset_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove source_ingest_asset_id field from catalog_asset table."""
    op.drop_column('catalog_asset', 'source_ingest_asset_id')
