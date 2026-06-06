"""add quality metrics to saved_reviews

Revision ID: 3035d61a420a
Revises: 3025d61a4209
Create Date: 2026-06-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3035d61a420a'
down_revision: Union[str, Sequence[str], None] = '3025d61a4209'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add quality_metrics JSON column to saved_reviews."""
    op.add_column('saved_reviews', sa.Column('quality_metrics', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove quality_metrics JSON column from saved_reviews."""
    op.drop_column('saved_reviews', 'quality_metrics')