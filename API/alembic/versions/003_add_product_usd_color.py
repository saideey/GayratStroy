"""Add USD prices, color, favorite to products

Revision ID: 003_add_product_usd_color
Revises: 002_add_usd_fields
Create Date: 2026-01-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_product_usd_color'
down_revision = '002_add_usd_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to products table
    op.add_column('products', sa.Column('sale_price_usd', sa.Numeric(20, 4), nullable=True))
    op.add_column('products', sa.Column('vip_price_usd', sa.Numeric(20, 4), nullable=True))
    op.add_column('products', sa.Column('color', sa.String(7), nullable=True))
    op.add_column('products', sa.Column('is_favorite', sa.Boolean(), default=False))
    op.add_column('products', sa.Column('sort_order', sa.Integer(), default=0))


def downgrade() -> None:
    op.drop_column('products', 'sort_order')
    op.drop_column('products', 'is_favorite')
    op.drop_column('products', 'color')
    op.drop_column('products', 'vip_price_usd')
    op.drop_column('products', 'sale_price_usd')
