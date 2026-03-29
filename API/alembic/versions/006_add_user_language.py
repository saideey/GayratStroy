"""Add language field to users

Revision ID: 006_add_user_language
Revises: 005_add_edit_tracking
Create Date: 2026-01-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rev_006'
down_revision = 'rev_005'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    exists = conn.execute(text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name='users' AND column_name='language'")).scalar()
    if exists:
        return
    # Add language column to users table with default 'uz'
    op.add_column('users', sa.Column('language', sa.String(10), nullable=False, server_default='uz'))


def downgrade():
    op.drop_column('users', 'language')
