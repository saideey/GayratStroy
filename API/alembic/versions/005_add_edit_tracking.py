"""Add edit and delete tracking fields

Revision ID: 005_add_edit_tracking
Revises: 004_add_telegram_id
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '005_add_edit_tracking'
down_revision = '004_add_telegram_id'
branch_labels = None
depends_on = None


def upgrade():
    # StockMovement - edit/delete tracking
    op.add_column('stock_movements', sa.Column('updated_by_id', sa.Integer(), nullable=True))
    op.add_column('stock_movements', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('stock_movements', sa.Column('deleted_by_id', sa.Integer(), nullable=True))
    op.add_column('stock_movements', sa.Column('deleted_at', sa.String(50), nullable=True))
    op.add_column('stock_movements', sa.Column('deleted_reason', sa.Text(), nullable=True))
    
    # Foreign keys for stock_movements
    op.create_foreign_key('fk_stock_movements_updated_by', 'stock_movements', 'users', ['updated_by_id'], ['id'])
    op.create_foreign_key('fk_stock_movements_deleted_by', 'stock_movements', 'users', ['deleted_by_id'], ['id'])
    
    # Sale - edit tracking
    op.add_column('sales', sa.Column('updated_by_id', sa.Integer(), nullable=True))
    op.add_column('sales', sa.Column('edit_reason', sa.Text(), nullable=True))
    
    # Foreign key for sales
    op.create_foreign_key('fk_sales_updated_by', 'sales', 'users', ['updated_by_id'], ['id'])


def downgrade():
    # Remove sale columns
    op.drop_constraint('fk_sales_updated_by', 'sales', type_='foreignkey')
    op.drop_column('sales', 'edit_reason')
    op.drop_column('sales', 'updated_by_id')
    
    # Remove stock_movements columns
    op.drop_constraint('fk_stock_movements_deleted_by', 'stock_movements', type_='foreignkey')
    op.drop_constraint('fk_stock_movements_updated_by', 'stock_movements', type_='foreignkey')
    op.drop_column('stock_movements', 'deleted_reason')
    op.drop_column('stock_movements', 'deleted_at')
    op.drop_column('stock_movements', 'deleted_by_id')
    op.drop_column('stock_movements', 'is_deleted')
    op.drop_column('stock_movements', 'updated_by_id')
