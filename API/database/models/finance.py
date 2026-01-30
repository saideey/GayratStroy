"""
Finance and Cash Register models.
Handles cash management, transactions, and financial tracking.
"""

from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Numeric, Date,
    ForeignKey, Enum, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from ..base import BaseModel


class CashRegister(BaseModel):
    """
    Cash register/point of sale.
    
    Each warehouse can have multiple registers.
    """
    
    __tablename__ = 'cash_registers'
    
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=True)
    
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # Current balance
    current_balance = Column(Numeric(20, 4), default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_open = Column(Boolean, default=False)  # Shift open/closed
    
    # Current shift info
    opened_at = Column(String(50), nullable=True)
    opened_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    opening_balance = Column(Numeric(20, 4), default=0)
    
    # Relationships
    warehouse = relationship("Warehouse")
    opened_by = relationship("User")
    transactions = relationship("CashTransaction", back_populates="cash_register", lazy="dynamic")
    
    __table_args__ = (
        Index('ix_cash_registers_warehouse_id', 'warehouse_id'),
        Index('ix_cash_registers_is_active', 'is_active'),
    )


class TransactionType(PyEnum):
    """Cash transaction types."""
    SALE = "sale"  # Sale payment received
    REFUND = "refund"  # Customer refund
    EXPENSE = "expense"  # General expense
    INCOME = "income"  # Other income
    DEPOSIT = "deposit"  # Cash deposit to bank
    WITHDRAWAL = "withdrawal"  # Cash from bank
    SUPPLIER_PAYMENT = "supplier_payment"  # Payment to supplier
    SALARY = "salary"  # Salary payment
    ADJUSTMENT = "adjustment"  # Manual adjustment
    TRANSFER_IN = "transfer_in"  # From another register
    TRANSFER_OUT = "transfer_out"  # To another register


class CashTransaction(BaseModel):
    """
    Cash register transactions.
    
    Records all cash movements for audit trail.
    """
    
    __tablename__ = 'cash_transactions'
    
    cash_register_id = Column(Integer, ForeignKey('cash_registers.id'), nullable=False)
    
    # Transaction details
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(20, 4), nullable=False)  # Positive for income, negative for expense
    
    # Balance tracking
    balance_before = Column(Numeric(20, 4), nullable=False)
    balance_after = Column(Numeric(20, 4), nullable=False)
    
    # Reference
    reference_type = Column(String(50), nullable=True)  # sale, payment, expense, etc.
    reference_id = Column(Integer, nullable=True)
    
    # Payment details
    payment_method = Column(String(20), nullable=True)  # cash, card, transfer
    
    # Description
    description = Column(Text, nullable=True)
    
    # Category for expenses
    category_id = Column(Integer, ForeignKey('expense_categories.id'), nullable=True)
    
    # Audit
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    cash_register = relationship("CashRegister", back_populates="transactions")
    category = relationship("ExpenseCategory")
    created_by = relationship("User")
    
    __table_args__ = (
        Index('ix_cash_transactions_register_id', 'cash_register_id'),
        Index('ix_cash_transactions_type', 'transaction_type'),
        Index('ix_cash_transactions_reference', 'reference_type', 'reference_id'),
        Index('ix_cash_transactions_created_at', 'created_at'),
    )


class ExpenseCategory(BaseModel):
    """
    Expense categories for tracking.
    """
    
    __tablename__ = 'expense_categories'
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('expense_categories.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    parent = relationship("ExpenseCategory", remote_side="ExpenseCategory.id", backref="children")
    
    __table_args__ = (
        Index('ix_expense_categories_parent_id', 'parent_id'),
    )


class CashShift(BaseModel):
    """
    Cash register shift tracking.
    
    Records shift open/close with summary.
    """
    
    __tablename__ = 'cash_shifts'
    
    cash_register_id = Column(Integer, ForeignKey('cash_registers.id'), nullable=False)
    
    # Shift period
    shift_date = Column(Date, nullable=False)
    opened_at = Column(String(50), nullable=False)
    closed_at = Column(String(50), nullable=True)
    
    # Opening/Closing
    opening_balance = Column(Numeric(20, 4), nullable=False)
    closing_balance = Column(Numeric(20, 4), nullable=True)
    
    # Summary
    total_sales = Column(Numeric(20, 4), default=0)
    total_refunds = Column(Numeric(20, 4), default=0)
    total_expenses = Column(Numeric(20, 4), default=0)
    total_income = Column(Numeric(20, 4), default=0)
    
    # Cash counted vs expected
    expected_cash = Column(Numeric(20, 4), nullable=True)
    actual_cash = Column(Numeric(20, 4), nullable=True)
    difference = Column(Numeric(20, 4), default=0)
    
    # Status
    status = Column(String(20), default='open')  # open, closed, reconciled
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    opened_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    closed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    cash_register = relationship("CashRegister")
    opened_by = relationship("User", foreign_keys=[opened_by_id])
    closed_by = relationship("User", foreign_keys=[closed_by_id])
    
    __table_args__ = (
        Index('ix_cash_shifts_register_id', 'cash_register_id'),
        Index('ix_cash_shifts_date', 'shift_date'),
        Index('ix_cash_shifts_status', 'status'),
    )


class BankAccount(BaseModel):
    """
    Company bank accounts for transfer tracking.
    """
    
    __tablename__ = 'bank_accounts'
    
    name = Column(String(200), nullable=False)
    bank_name = Column(String(200), nullable=False)
    account_number = Column(String(50), nullable=False, unique=True)
    mfo = Column(String(20), nullable=True)
    
    # Current balance (updated periodically)
    current_balance = Column(Numeric(20, 4), default=0)
    last_balance_update = Column(String(50), nullable=True)
    
    # Currency
    currency = Column(String(10), default='UZS')
    
    # Status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('ix_bank_accounts_is_active', 'is_active'),
    )


class BankTransaction(BaseModel):
    """
    Bank account transactions.
    """
    
    __tablename__ = 'bank_transactions'
    
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id'), nullable=False)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # deposit, withdrawal, transfer, fee
    amount = Column(Numeric(20, 4), nullable=False)
    
    # Balance tracking
    balance_before = Column(Numeric(20, 4), nullable=False)
    balance_after = Column(Numeric(20, 4), nullable=False)
    
    # External reference
    bank_reference = Column(String(100), nullable=True)
    transaction_date = Column(Date, nullable=False)
    
    # Reference to internal document
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    counterparty = Column(String(300), nullable=True)  # Who the payment is from/to
    
    # Audit
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    bank_account = relationship("BankAccount")
    created_by = relationship("User")
    
    __table_args__ = (
        Index('ix_bank_transactions_account_id', 'bank_account_id'),
        Index('ix_bank_transactions_date', 'transaction_date'),
        Index('ix_bank_transactions_type', 'transaction_type'),
    )


class DailyReport(BaseModel):
    """
    Daily financial summary report.
    Pre-calculated for faster reporting.
    """
    
    __tablename__ = 'daily_reports'
    
    report_date = Column(Date, nullable=False, unique=True)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=True)  # Null for total
    
    # Sales
    total_sales = Column(Numeric(20, 4), default=0)
    total_sales_count = Column(Integer, default=0)
    total_items_sold = Column(Integer, default=0)
    
    # Discounts
    total_discounts = Column(Numeric(20, 4), default=0)
    
    # Returns
    total_returns = Column(Numeric(20, 4), default=0)
    total_returns_count = Column(Integer, default=0)
    
    # Payments
    cash_received = Column(Numeric(20, 4), default=0)
    card_received = Column(Numeric(20, 4), default=0)
    transfer_received = Column(Numeric(20, 4), default=0)
    debt_issued = Column(Numeric(20, 4), default=0)
    debt_collected = Column(Numeric(20, 4), default=0)
    
    # Cost and Profit
    total_cost = Column(Numeric(20, 4), default=0)
    gross_profit = Column(Numeric(20, 4), default=0)
    
    # Expenses
    total_expenses = Column(Numeric(20, 4), default=0)
    
    # Net result
    net_result = Column(Numeric(20, 4), default=0)
    
    # Relationships
    warehouse = relationship("Warehouse")
    
    __table_args__ = (
        Index('ix_daily_reports_date', 'report_date'),
        Index('ix_daily_reports_warehouse', 'warehouse_id'),
    )
