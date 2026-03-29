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

    # Enum type — xavfsiz yaratish
    conn = op.get_bind()
    conn.execute(text(
        "DO $$ BEGIN "
        "  CREATE TYPE suppliertransactiontype AS ENUM ('debt', 'payment', 'return'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    ))

    # Raw SQL — SQLAlchemy enum auto-create muammosini oldini olish
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS supplier_transactions (
            id SERIAL PRIMARY KEY,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            transaction_type suppliertransactiontype NOT NULL,
            amount NUMERIC(20, 2) NOT NULL,
            currency VARCHAR(5) NOT NULL DEFAULT 'uzs',
            usd_rate NUMERIC(12, 2),
            amount_uzs NUMERIC(20, 2),
            transaction_date DATE NOT NULL,
            comment TEXT NOT NULL,
            purchase_order_id INTEGER REFERENCES purchase_orders(id),
            is_deleted BOOLEAN NOT NULL DEFAULT false,
            deleted_at TIMESTAMP,
            deleted_by_id INTEGER REFERENCES users(id),
            delete_comment TEXT,
            created_by_id INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_transactions_supplier_id ON supplier_transactions (supplier_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_transactions_type ON supplier_transactions (transaction_type)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_transactions_date ON supplier_transactions (transaction_date)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_transactions_is_deleted ON supplier_transactions (is_deleted)"))


def downgrade() -> None:
    if table_exists('supplier_transactions'):
        op.drop_table('supplier_transactions')
    op.execute(text("DROP TYPE IF EXISTS suppliertransactiontype"))
