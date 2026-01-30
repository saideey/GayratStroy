"""Add language field to users

Revision ID: 006_add_user_language
Revises: 005_add_edit_tracking
Create Date: 2026-01-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_user_language'
down_revision = '005_add_edit_tracking'
branch_labels = None
depends_on = None


def upgrade():
    # Add language column to users table with default 'uz'
    op.add_column('users', sa.Column('language', sa.String(10), nullable=False, server_default='uz'))


def downgrade():
    op.drop_column('users', 'language')
