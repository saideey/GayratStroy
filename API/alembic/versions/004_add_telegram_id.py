"""Add telegram_id to customers

Revision ID: 004_add_telegram_id
Revises: 003_add_product_usd_color
Create Date: 2026-01-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'rev_004'
down_revision = 'rev_003'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    exists = conn.execute(text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name='customers' AND column_name='telegram_id'")).scalar()
    if exists:
        return
    op.add_column('customers', sa.Column('telegram_id', sa.String(50), nullable=True))
    op.create_index('ix_customers_telegram_id', 'customers', ['telegram_id'])


def downgrade():
    op.drop_index('ix_customers_telegram_id', table_name='customers')
    op.drop_column('customers', 'telegram_id')
