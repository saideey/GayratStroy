"""
Expense (Chiqimlar) models.
Barcha xarajatlarni kategoriyalar bo'yicha kuzatish.
Har bir o'zgartirish tarixi saqlanadi (audit log).
"""

from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Numeric,
    ForeignKey, Enum, Index, Date
)
from sqlalchemy.orm import relationship

from ..base import BaseModel, SoftDeleteMixin


class ExpenseCurrencyType(PyEnum):
    """Valyuta turlari."""
    UZS = "uzs"
    USD = "usd"


class ExpenseEditAction(PyEnum):
    """Audit log uchun harakat turlari."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RESTORED = "restored"


class ExpenseCategory(BaseModel):
    """
    Chiqim kategoriyalari.
    Misol: Elektr energiyasi, Ijara, Maosh, Transport...
    """

    __tablename__ = 'expense_categories'

    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True, default='#6366f1')
    icon = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    expenses = relationship(
        "Expense",
        back_populates="category",
        foreign_keys="Expense.category_id"
    )

    __table_args__ = (
        Index('ix_expense_categories_is_active', 'is_active'),
    )

    def __repr__(self):
        return f"<ExpenseCategory(id={self.id}, name={self.name})>"


class Expense(BaseModel, SoftDeleteMixin):
    """
    Chiqim (xarajat) yozuvi.

    Soft-delete qo'llab-quvvatlanadi:
    - o'chirilganda is_deleted=True, deleted_at va deleted_by_id to'ldiriladi
    - haqiqiy o'chirish hech qachon bo'lmaydi
    """

    __tablename__ = 'expenses'

    # Asosiy ma'lumotlar
    title = Column(String(255), nullable=False)             # Sarlavha
    description = Column(Text, nullable=True)               # Izoh
    amount = Column(Numeric(20, 2), nullable=False)         # Summa
    currency = Column(
        Enum(ExpenseCurrencyType),
        nullable=False,
        default=ExpenseCurrencyType.UZS
    )
    usd_rate = Column(Numeric(12, 2), nullable=True)        # 1 USD = ? UZS (agar USD bo'lsa)
    amount_uzs = Column(Numeric(20, 2), nullable=True)      # So'mga konvertatsiya (USD bo'lsa)

    expense_date = Column(Date, nullable=False)             # Chiqim sanasi

    # Kategoriya
    category_id = Column(
        Integer,
        ForeignKey('expense_categories.id'),
        nullable=False
    )

    # Kim yozdi
    created_by_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False
    )

    # Kim o'chirdi (soft delete)
    deleted_by_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=True
    )
    delete_comment = Column(Text, nullable=True)            # O'chirishda izoh majburiy

    # Relationships
    category = relationship("ExpenseCategory", back_populates="expenses", foreign_keys=[category_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
    edit_logs = relationship(
        "ExpenseEditLog",
        back_populates="expense",
        order_by="ExpenseEditLog.id.desc()"
    )

    __table_args__ = (
        Index('ix_expenses_category_id', 'category_id'),
        Index('ix_expenses_expense_date', 'expense_date'),
        Index('ix_expenses_created_by_id', 'created_by_id'),
        Index('ix_expenses_is_deleted', 'is_deleted'),
        Index('ix_expenses_currency', 'currency'),
    )

    def __repr__(self):
        return f"<Expense(id={self.id}, title={self.title}, amount={self.amount})>"


class ExpenseEditLog(BaseModel):
    """
    Chiqim o'zgartirish tarixi (audit log).

    Har bir create/update/delete uchun yozuv saqlanadi.
    Eski qiymatlar JSON formatda saqlanadi.
    """

    __tablename__ = 'expense_edit_logs'

    expense_id = Column(
        Integer,
        ForeignKey('expenses.id'),
        nullable=False
    )

    # Kim o'zgartirdi
    changed_by_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False
    )

    # Harakat turi
    action = Column(
        Enum(ExpenseEditAction),
        nullable=False
    )

    # Majburiy izoh (update va delete uchun)
    comment = Column(Text, nullable=False)

    # Eski qiymatlar (JSON string)
    old_title = Column(String(255), nullable=True)
    old_description = Column(Text, nullable=True)
    old_amount = Column(Numeric(20, 2), nullable=True)
    old_currency = Column(String(10), nullable=True)
    old_category_id = Column(Integer, nullable=True)
    old_expense_date = Column(Date, nullable=True)

    # Yangi qiymatlar
    new_title = Column(String(255), nullable=True)
    new_description = Column(Text, nullable=True)
    new_amount = Column(Numeric(20, 2), nullable=True)
    new_currency = Column(String(10), nullable=True)
    new_category_id = Column(Integer, nullable=True)
    new_expense_date = Column(Date, nullable=True)

    # Relationships
    expense = relationship("Expense", back_populates="edit_logs")
    changed_by = relationship("User", foreign_keys=[changed_by_id])

    __table_args__ = (
        Index('ix_expense_edit_logs_expense_id', 'expense_id'),
        Index('ix_expense_edit_logs_changed_by_id', 'changed_by_id'),
        Index('ix_expense_edit_logs_action', 'action'),
    )

    def __repr__(self):
        return f"<ExpenseEditLog(id={self.id}, expense_id={self.expense_id}, action={self.action})>"
