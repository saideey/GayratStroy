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
        # Enum type yaratish (agar yo'q bo'lsa)
        conn.execute(text(
            "DO $$ BEGIN "
            "  CREATE TYPE expensecurrencytype AS ENUM ('uzs', 'usd'); "
            "EXCEPTION WHEN duplicate_object THEN NULL; "
            "END $$;"
        ))

        op.create_table(
            'expenses',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('amount', sa.Numeric(20, 2), nullable=False),
            sa.Column('currency',
                sa.Enum('uzs', 'usd', name='expensecurrencytype', create_type=False),
                nullable=False,
                server_default='uzs'
            ),
            sa.Column('usd_rate', sa.Numeric(12, 2), nullable=True),
            sa.Column('amount_uzs', sa.Numeric(20, 2), nullable=True),
            sa.Column('expense_date', sa.Date(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.Column('created_by_id', sa.Integer(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_by_id', sa.Integer(), nullable=True),
            sa.Column('delete_comment', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['category_id'], ['expense_categories.id']),
            sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
            sa.ForeignKeyConstraint(['deleted_by_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_expenses_category_id', 'expenses', ['category_id'])
        op.create_index('ix_expenses_expense_date', 'expenses', ['expense_date'])
        op.create_index('ix_expenses_created_by_id', 'expenses', ['created_by_id'])
        op.create_index('ix_expenses_is_deleted', 'expenses', ['is_deleted'])
        op.create_index('ix_expenses_currency', 'expenses', ['currency'])

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

        op.create_table(
            'expense_edit_logs',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('expense_id', sa.Integer(), nullable=False),
            sa.Column('changed_by_id', sa.Integer(), nullable=False),
            sa.Column('action',
                sa.Enum('created', 'updated', 'deleted', 'restored',
                        name='expenseeditaction', create_type=False),
                nullable=False
            ),
            sa.Column('comment', sa.Text(), nullable=False),
            sa.Column('old_title', sa.String(255), nullable=True),
            sa.Column('old_description', sa.Text(), nullable=True),
            sa.Column('old_amount', sa.Numeric(20, 2), nullable=True),
            sa.Column('old_currency', sa.String(10), nullable=True),
            sa.Column('old_category_id', sa.Integer(), nullable=True),
            sa.Column('old_expense_date', sa.Date(), nullable=True),
            sa.Column('new_title', sa.String(255), nullable=True),
            sa.Column('new_description', sa.Text(), nullable=True),
            sa.Column('new_amount', sa.Numeric(20, 2), nullable=True),
            sa.Column('new_currency', sa.String(10), nullable=True),
            sa.Column('new_category_id', sa.Integer(), nullable=True),
            sa.Column('new_expense_date', sa.Date(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['expense_id'], ['expenses.id']),
            sa.ForeignKeyConstraint(['changed_by_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_expense_edit_logs_expense_id', 'expense_edit_logs', ['expense_id'])
        op.create_index('ix_expense_edit_logs_changed_by_id', 'expense_edit_logs', ['changed_by_id'])
        op.create_index('ix_expense_edit_logs_action', 'expense_edit_logs', ['action'])

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
