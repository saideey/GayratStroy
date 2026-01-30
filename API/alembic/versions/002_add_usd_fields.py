"""Add USD fields to stock_movements and stock tables

Revision ID: 002_add_usd_fields
Revises: 001_initial
Create Date: 2026-01-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_usd_fields'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to stock_movements table
    op.add_column('stock_movements', sa.Column('supplier_name', sa.String(200), nullable=True))
    op.add_column('stock_movements', sa.Column('unit_price_usd', sa.Numeric(20, 4), nullable=True))
    op.add_column('stock_movements', sa.Column('exchange_rate', sa.Numeric(20, 4), nullable=True))
    
    # Add USD cost tracking to stock table
    op.add_column('stock', sa.Column('last_purchase_cost_usd', sa.Numeric(20, 4), nullable=True))


def downgrade() -> None:
    op.drop_column('stock', 'last_purchase_cost_usd')
    op.drop_column('stock_movements', 'exchange_rate')
    op.drop_column('stock_movements', 'unit_price_usd')
    op.drop_column('stock_movements', 'supplier_name')
