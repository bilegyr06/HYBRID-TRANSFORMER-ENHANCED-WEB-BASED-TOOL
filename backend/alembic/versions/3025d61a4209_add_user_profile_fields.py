"""add user profile fields

Revision ID: 3025d61a4209
Revises: 3015d61a4208
Create Date: 2026-05-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3025d61a4209'
down_revision = '3015d61a4208'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add profile enhancement fields to users table."""
    # Add new columns with defaults
    op.add_column('users', sa.Column('bio', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('organization', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('users', sa.Column('preferences', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('profile_updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove profile enhancement fields from users table."""
    op.drop_column('users', 'profile_updated_at')
    op.drop_column('users', 'preferences')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'organization')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'bio')
