"""add_supplier_id_to_movements_and_purchase_order

Revision ID: 009_supplier_purchase_integration
Revises: 008_add_supplier_transactions
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'rev_009'
down_revision = 'rev_008'
branch_labels = None
depends_on = None


def column_exists(table, column):
    conn = op.get_bind()
    return conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name=:t AND column_name=:c"
    ), {"t": table, "c": column}).scalar() > 0


def upgrade() -> None:
    # ── stock_movements ga supplier_id qo'shish ──────────────────────────────
    if not column_exists('stock_movements', 'supplier_id'):
        op.add_column('stock_movements',
            sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id'), nullable=True)
        )
        op.create_index('ix_stock_movements_supplier_id', 'stock_movements', ['supplier_id'])

    # ── purchase_orders ga to'lov maydonlari ─────────────────────────────────
    if not column_exists('purchase_orders', 'paid_at_receipt'):
        op.add_column('purchase_orders',
            sa.Column('paid_at_receipt', sa.Numeric(20, 2), nullable=True, server_default='0')
        )
    if not column_exists('purchase_orders', 'payment_type'):
        op.add_column('purchase_orders',
            sa.Column('payment_type', sa.String(20), nullable=True)
        )
    if not column_exists('purchase_orders', 'payment_comment'):
        op.add_column('purchase_orders',
            sa.Column('payment_comment', sa.Text(), nullable=True)
        )
    if not column_exists('purchase_orders', 'supplier_transaction_id'):
        op.add_column('purchase_orders',
            sa.Column('supplier_transaction_id', sa.Integer(),
                      sa.ForeignKey('supplier_transactions.id'), nullable=True)
        )


def downgrade() -> None:
    if column_exists('stock_movements', 'supplier_id'):
        op.drop_index('ix_stock_movements_supplier_id', 'stock_movements')
        op.drop_column('stock_movements', 'supplier_id')
    for col in ['supplier_transaction_id', 'payment_comment', 'payment_type', 'paid_at_receipt']:
        if column_exists('purchase_orders', col):
            op.drop_column('purchase_orders', col)
