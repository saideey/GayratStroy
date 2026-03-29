"""add_supplier_transactions

Revision ID: 008_add_supplier_transactions
Revises: 007_add_expenses
Create Date: 2026-03-28

Ta'minotchilar bilan hisob-kitob tarixi jadvali.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'rev_008'
down_revision = 'rev_007'
branch_labels = None
depends_on = None


def table_exists(name):
    conn = op.get_bind()
    return conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name=:n"
    ), {"n": name}).scalar() > 0


def upgrade() -> None:
    if table_exists('supplier_transactions'):
        return

    # Enum type
    conn = op.get_bind()
    conn.execute(text(
        "DO $$ BEGIN "
        "  CREATE TYPE suppliertransactiontype AS ENUM ('debt', 'payment', 'return'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    ))

    op.create_table(
        'supplier_transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type',
            sa.Enum('debt', 'payment', 'return',
                    name='suppliertransactiontype', create_type=False),
            nullable=False
        ),
        sa.Column('amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('currency', sa.String(5), nullable=False, server_default='uzs'),
        sa.Column('usd_rate', sa.Numeric(12, 2), nullable=True),
        sa.Column('amount_uzs', sa.Numeric(20, 2), nullable=True),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=True),
        # Soft delete
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by_id', sa.Integer(), nullable=True),
        sa.Column('delete_comment', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id']),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_supplier_transactions_supplier_id', 'supplier_transactions', ['supplier_id'])
    op.create_index('ix_supplier_transactions_type', 'supplier_transactions', ['transaction_type'])
    op.create_index('ix_supplier_transactions_date', 'supplier_transactions', ['transaction_date'])
    op.create_index('ix_supplier_transactions_is_deleted', 'supplier_transactions', ['is_deleted'])


def downgrade() -> None:
    if table_exists('supplier_transactions'):
        op.drop_table('supplier_transactions')
    op.execute(text("DROP TYPE IF EXISTS suppliertransactiontype"))
