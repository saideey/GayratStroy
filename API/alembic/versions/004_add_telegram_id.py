"""Add telegram_id to customers

Revision ID: 004_add_telegram_id
Revises: 003_add_product_usd_color
Create Date: 2026-01-19
"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_telegram_id'
down_revision = '003_add_product_usd_color'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('customers', sa.Column('telegram_id', sa.String(50), nullable=True))
    op.create_index('ix_customers_telegram_id', 'customers', ['telegram_id'])


def downgrade():
    op.drop_index('ix_customers_telegram_id', table_name='customers')
    op.drop_column('customers', 'telegram_id')
