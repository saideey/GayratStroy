"""
Customer and CRM models.
Supports regular and VIP customers with debt/credit tracking.
"""

from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Numeric, Date,
    ForeignKey, Enum, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from ..base import BaseModel, SoftDeleteMixin


class CustomerType(PyEnum):
    """Customer types."""
    REGULAR = "regular"  # Oddiy mijoz
    VIP = "vip"  # Premium klient
    WHOLESALE = "wholesale"  # Ulgurji xaridor
    CONTRACTOR = "contractor"  # Pudratchi/Qurilish kompaniyasi


class Customer(BaseModel, SoftDeleteMixin):
    """
    Customer model with VIP support and debt tracking.
    
    Features:
    - Regular and VIP customer types
    - Login/password for VIP personal cabinet
    - Debt and advance balance tracking
    - Purchase history
    """
    
    __tablename__ = 'customers'
    
    # Basic info
    name = Column(String(300), nullable=False, index=True)
    company_name = Column(String(300), nullable=True)  # Kompaniya nomi
    phone = Column(String(20), nullable=False, index=True)
    phone_secondary = Column(String(20), nullable=True)
    telegram_id = Column(String(50), nullable=True, index=True)  # Telegram ID
    email = Column(String(255), nullable=True, index=True)
    address = Column(Text, nullable=True)
    
    # Customer type and status
    customer_type = Column(Enum(CustomerType), default=CustomerType.REGULAR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # VIP credentials (for personal cabinet)
    login = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    
    # Financial info
    credit_limit = Column(Numeric(20, 4), default=0)  # Maksimal qarz limiti
    current_debt = Column(Numeric(20, 4), default=0)  # Joriy qarz
    advance_balance = Column(Numeric(20, 4), default=0)  # Oldindan to'langan summa (avans)
    
    # Statistics
    total_purchases = Column(Numeric(20, 4), default=0)  # Umumiy xarid summasi
    total_purchases_count = Column(Integer, default=0)  # Xaridlar soni
    last_purchase_date = Column(Date, nullable=True)
    
    # Discount settings
    personal_discount_percent = Column(Numeric(5, 2), default=0)  # Shaxsiy chegirma %
    
    # Additional info
    inn = Column(String(50), nullable=True)  # INN (soliq raqami)
    notes = Column(Text, nullable=True)
    
    # Notification preferences
    sms_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=False)
    
    # Assigned manager
    manager_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    manager = relationship("User", foreign_keys=[manager_id])
    sales = relationship("Sale", back_populates="customer", lazy="dynamic")
    payments = relationship("Payment", back_populates="customer", lazy="dynamic")
    debt_records = relationship("CustomerDebt", back_populates="customer", lazy="dynamic")
    
    __table_args__ = (
        Index('ix_customers_type', 'customer_type'),
        Index('ix_customers_is_active', 'is_active'),
        Index('ix_customers_manager_id', 'manager_id'),
        CheckConstraint('current_debt >= 0', name='ck_customer_debt_non_negative'),
        CheckConstraint('advance_balance >= 0', name='ck_customer_advance_non_negative'),
    )
    
    @property
    def available_credit(self):
        """Get available credit amount."""
        return max(0, self.credit_limit - self.current_debt + self.advance_balance)
    
    @property
    def is_vip(self) -> bool:
        """Check if customer is VIP."""
        return self.customer_type == CustomerType.VIP
    
    def can_purchase_on_credit(self, amount) -> bool:
        """Check if customer can purchase given amount on credit."""
        return amount <= self.available_credit


class CustomerDebt(BaseModel):
    """
    Customer debt transaction records.
    
    Tracks all debt creation and payment events.
    """
    
    __tablename__ = 'customer_debts'
    
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Transaction type
    transaction_type = Column(String(20), nullable=False)  # debt, payment, advance
    
    # Amounts
    amount = Column(Numeric(20, 4), nullable=False)  # Positive for debt, negative for payment
    balance_before = Column(Numeric(20, 4), nullable=False)  # Debt before transaction
    balance_after = Column(Numeric(20, 4), nullable=False)  # Debt after transaction
    
    # Reference
    reference_type = Column(String(50), nullable=True)  # sale, payment, adjustment
    reference_id = Column(Integer, nullable=True)
    
    # Notes
    description = Column(Text, nullable=True)
    
    # Audit
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="debt_records")
    created_by = relationship("User")
    
    __table_args__ = (
        Index('ix_customer_debts_customer_id', 'customer_id'),
        Index('ix_customer_debts_type', 'transaction_type'),
        Index('ix_customer_debts_reference', 'reference_type', 'reference_id'),
        Index('ix_customer_debts_created_at', 'created_at'),
    )


class CustomerGroup(BaseModel, SoftDeleteMixin):
    """
    Customer groups for bulk discounts and categorization.
    """
    
    __tablename__ = 'customer_groups'
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    discount_percent = Column(Numeric(5, 2), default=0)  # Group discount
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('ix_customer_groups_is_active', 'is_active'),
    )


class CustomerGroupMember(BaseModel):
    """
    Customer membership in groups.
    A customer can belong to multiple groups.
    """
    
    __tablename__ = 'customer_group_members'
    
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('customer_groups.id'), nullable=False)
    
    # Relationships
    customer = relationship("Customer")
    group = relationship("CustomerGroup")
    
    __table_args__ = (
        Index('ix_cgm_customer_id', 'customer_id'),
        Index('ix_cgm_group_id', 'group_id'),
    )


class LoyaltyPoints(BaseModel):
    """
    Customer loyalty points tracking.
    Optional module for loyalty program.
    """
    
    __tablename__ = 'loyalty_points'
    
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Transaction
    points = Column(Integer, nullable=False)  # Positive for earn, negative for redeem
    transaction_type = Column(String(20), nullable=False)  # earn, redeem, expire, adjust
    
    # Reference
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    
    # Balance tracking
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    
    # Notes
    description = Column(Text, nullable=True)
    expires_at = Column(Date, nullable=True)
    
    # Relationships
    customer = relationship("Customer")
    
    __table_args__ = (
        Index('ix_loyalty_points_customer_id', 'customer_id'),
        Index('ix_loyalty_points_type', 'transaction_type'),
        Index('ix_loyalty_points_created_at', 'created_at'),
    )


class CustomerAddress(BaseModel, SoftDeleteMixin):
    """
    Multiple delivery addresses for customers.
    """
    
    __tablename__ = 'customer_addresses'
    
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Address details
    address_type = Column(String(20), default='delivery')  # delivery, billing, office
    address_name = Column(String(100), nullable=True)  # e.g., "Uy", "Ofis", "Ob'yekt"
    
    # Full address
    region = Column(String(100), nullable=True)  # Viloyat
    city = Column(String(100), nullable=True)  # Shahar
    district = Column(String(100), nullable=True)  # Tuman
    street = Column(String(200), nullable=True)
    building = Column(String(50), nullable=True)
    apartment = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Coordinates for delivery
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    
    # Contact at this address
    contact_name = Column(String(200), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    
    # Flags
    is_default = Column(Boolean, default=False)
    delivery_notes = Column(Text, nullable=True)
    
    # Relationships
    customer = relationship("Customer")
    
    __table_args__ = (
        Index('ix_customer_addresses_customer_id', 'customer_id'),
        Index('ix_customer_addresses_type', 'address_type'),
    )
