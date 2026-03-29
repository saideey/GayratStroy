"""add_expenses_module

Revision ID: 007_add_expenses
Revises: 006_add_user_language
Create Date: 2026-03-28

Bu migration:
  1. expense_categories ga color, icon, parent_id ustunlarini qo'shadi (agar yo'q bo'lsa)
  2. expenses jadvalini yaratadi
  3. expense_edit_logs jadvalini yaratadi
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'rev_007'
down_revision = 'rev_006'
branch_labels = None
depends_on = None


def column_exists(table, column):
    """Check if column exists in table."""
    conn = op.get_bind()
    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name=:t AND column_name=:c"
    ), {"t": table, "c": column})
    return result.scalar() > 0


def upgrade() -> None:

    # ─── 1. expense_categories ga yangi ustunlar (agar yo'q bo'lsa) ──────────
    if not column_exists('expense_categories', 'color'):
        op.add_column('expense_categories',
            sa.Column('color', sa.String(7), nullable=True)
        )

    if not column_exists('expense_categories', 'icon'):
        op.add_column('expense_categories',
            sa.Column('icon', sa.String(50), nullable=True)
        )

    # Mavjud kategoriyalarga default rang
    op.execute("UPDATE expense_categories SET color = '#6b7280' WHERE color IS NULL")

    # ─── 2. expenses jadvali ─────────────────────────────────────────────────
    conn = op.get_bind()
    table_exists = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_name='expenses'"
    )).scalar()

    if not table_exists:
        # Enum type yaratish — IF NOT EXISTS bilan xavfsiz
        conn.execute(text(
            "DO $$ BEGIN "
            "  CREATE TYPE expensecurrencytype AS ENUM ('uzs', 'usd'); "
            "EXCEPTION WHEN duplicate_object THEN NULL; "
            "END $$;"
        ))

        # Raw SQL ishlatamiz — SQLAlchemy enum auto-create muammosini oldini olish uchun
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                amount NUMERIC(20, 2) NOT NULL,
                currency expensecurrencytype NOT NULL DEFAULT 'uzs',
                usd_rate NUMERIC(12, 2),
                amount_uzs NUMERIC(20, 2),
                expense_date DATE NOT NULL,
                category_id INTEGER NOT NULL REFERENCES expense_categories(id),
                created_by_id INTEGER NOT NULL REFERENCES users(id),
                is_deleted BOOLEAN NOT NULL DEFAULT false,
                deleted_at TIMESTAMP,
                deleted_by_id INTEGER REFERENCES users(id),
                delete_comment TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_expenses_category_id ON expenses (category_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_expenses_expense_date ON expenses (expense_date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_expenses_created_by_id ON expenses (created_by_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_expenses_is_deleted ON expenses (is_deleted)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_expenses_currency ON expenses (currency)"))

    # ─── 3. expense_edit_logs jadvali ────────────────────────────────────────
    logs_exists = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_name='expense_edit_logs'"
    )).scalar()

    if not logs_exists:
        conn.execute(text(
            "DO $$ BEGIN "
            "  CREATE TYPE expenseeditaction AS ENUM ('created', 'updated', 'deleted', 'restored'); "
            "EXCEPTION WHEN duplicate_object THEN NULL; "
            "END $$;"
        ))

        # Raw SQL — enum auto-create muammosini oldini olish
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS expense_edit_logs (
                id SERIAL PRIMARY KEY,
                expense_id INTEGER NOT NULL REFERENCES expenses(id),
                changed_by_id INTEGER NOT NULL REFERENCES users(id),
                action expenseeditaction NOT NULL,
                comment TEXT NOT NULL,
                old_title VARCHAR(255),
                old_description TEXT,
                old_amount NUMERIC(20, 2),
                old_currency VARCHAR(10),
                old_category_id INTEGER,
                old_expense_date DATE,
                new_title VARCHAR(255),
                new_description TEXT,
                new_amount NUMERIC(20, 2),
                new_currency VARCHAR(10),
                new_category_id INTEGER,
                new_expense_date DATE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_expense_edit_logs_expense_id ON expense_edit_logs (expense_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_expense_edit_logs_changed_by_id ON expense_edit_logs (changed_by_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_expense_edit_logs_action ON expense_edit_logs (action)"))

    # ─── 4. Default kategoriyalar ────────────────────────────────────────────
    op.execute("""
        INSERT INTO expense_categories (name, description, color, icon, is_active, created_at, updated_at)
        SELECT v.name, v.description, v.color, v.icon, true, NOW(), NOW()
        FROM (VALUES
            ('Elektr energiyasi', 'Elektr energiyasi to''lovi', '#f59e0b', '⚡'),
            ('Ijara', 'Do''kon yoki ombor ijarasi', '#8b5cf6', '🏠'),
            ('Maosh', 'Xodimlar maoshi', '#10b981', '👥'),
            ('Transport', 'Transport va yuk tashish', '#3b82f6', '🚛'),
            ('Internet va aloqa', 'Internet, telefon to''lovlari', '#06b6d4', '📡'),
            ('Ta''mirlash', 'Jihozlar va binoni ta''mirlash', '#ef4444', '🔧'),
            ('Boshqa', 'Boshqa xarajatlar', '#6b7280', '📋')
        ) AS v(name, description, color, icon)
        WHERE NOT EXISTS (
            SELECT 1 FROM expense_categories ec WHERE ec.name = v.name
        )
    """)


def downgrade() -> None:
    conn = op.get_bind()

    logs_exists = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='expense_edit_logs'"
    )).scalar()
    if logs_exists:
        op.drop_table('expense_edit_logs')

    expenses_exists = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='expenses'"
    )).scalar()
    if expenses_exists:
        op.drop_table('expenses')

    if column_exists('expense_categories', 'icon'):
        op.drop_column('expense_categories', 'icon')
    if column_exists('expense_categories', 'color'):
        op.drop_column('expense_categories', 'color')

    conn.execute(text("DROP TYPE IF EXISTS expensecurrencytype"))
    conn.execute(text("DROP TYPE IF EXISTS expenseeditaction"))
