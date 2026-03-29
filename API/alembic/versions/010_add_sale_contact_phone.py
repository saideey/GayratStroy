"""Add contact_phone to sales table

Revision ID: rev_010
Revises: rev_009
Create Date: 2026-03-29

Mijoz tanlanmasa ham sotuv paytida kiritilgan telefon raqamni saqlash uchun.
"""
from alembic import op
import sqlalchemy as sa

revision = 'rev_010'
down_revision = 'rev_009'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'sales',
        sa.Column(
            'contact_phone',
            sa.String(50),
            nullable=True,
            comment='Mijoz tanlanmasa kiritilgan telefon raqami (kassir uchun)'
        )
    )


def downgrade():
    op.drop_column('sales', 'contact_phone')
