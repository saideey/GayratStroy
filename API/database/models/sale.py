"""
Sale, Payment, and related models.
Handles sales transactions with proportional discount distribution.

Key feature: When seller changes total amount, system distributes 
discount proportionally across all items.
"""

from enum import Enum as PyEnum
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Numeric, Date,
    ForeignKey, Enum, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from ..base import BaseModel


class PaymentStatus(PyEnum):
    """Sale payment status."""
    PENDING = "pending"  # Kutilmoqda
    PARTIAL = "partial"  # Qisman to'langan
    PAID = "paid"  # To'liq to'langan
    DEBT = "debt"  # Qarzga
    CANCELLED = "cancelled"  # Bekor qilingan
    REFUNDED = "refunded"  # Qaytarilgan


class PaymentType(PyEnum):
    """Payment methods."""
    CASH = "cash"  # Naqd
    CARD = "card"  # Karta
    TRANSFER = "transfer"  # O'tkazma
    DEBT = "debt"  # Qarzga
    MIXED = "mixed"  # Aralash


class Sale(BaseModel):
    """
    Sale transaction header.
    
    Key features:
    - Supports total amount override with proportional discount
    - Tracks both original and final prices
    - Multiple payment types support
    - Debt tracking
    """
    
    __tablename__ = 'sales'
    
    # Reference number
    sale_number = Column(String(50), unique=True, nullable=False, index=True)
    sale_date = Column(Date, nullable=False)
    
    # Parties
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)  # Can be anonymous
    seller_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # Amounts
    subtotal = Column(Numeric(20, 4), nullable=False)  # Sum before discount (catalog prices)
    discount_amount = Column(Numeric(20, 4), default=0)  # Total discount amount
    discount_percent = Column(Numeric(5, 2), default=0)  # Overall discount percentage
    total_amount = Column(Numeric(20, 4), nullable=False)  # Final amount after discount
    
    # Payment tracking
    paid_amount = Column(Numeric(20, 4), default=0)  # Amount already paid
    debt_amount = Column(Numeric(20, 4), default=0)  # Amount on credit
    
    # Status
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=True)  # Primary payment type
    
    # Additional info
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Only for staff
    
    # Delivery info
    requires_delivery = Column(Boolean, default=False)
    delivery_address = Column(Text, nullable=True)
    delivery_date = Column(Date, nullable=True)
    delivery_cost = Column(Numeric(20, 4), default=0)
    
    # Flags
    is_vip_sale = Column(Boolean, default=False)  # VIP prices applied
    is_wholesale = Column(Boolean, default=False)  # Wholesale sale
    is_cancelled = Column(Boolean, default=False)
    cancelled_reason = Column(Text, nullable=True)
    cancelled_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    cancelled_at = Column(String(50), nullable=True)
    
    # Edit tracking
    updated_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    edit_reason = Column(Text, nullable=True)
    
    # Approval for large discounts
    discount_approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # SMS sent flag
    sms_sent = Column(Boolean, default=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="sales")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="sales")
    warehouse = relationship("Warehouse")
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    discount_approved_by = relationship("User", foreign_keys=[discount_approved_by_id])
    items = relationship("SaleItem", back_populates="sale", lazy="dynamic", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sale", lazy="dynamic")
    
    __table_args__ = (
        Index('ix_sales_customer_id', 'customer_id'),
        Index('ix_sales_seller_id', 'seller_id'),
        Index('ix_sales_warehouse_id', 'warehouse_id'),
        Index('ix_sales_sale_date', 'sale_date'),
        Index('ix_sales_payment_status', 'payment_status'),
        Index('ix_sales_created_at', 'created_at'),
        CheckConstraint('total_amount >= 0', name='ck_sale_total_non_negative'),
        CheckConstraint('discount_percent >= 0 AND discount_percent <= 100', name='ck_sale_discount_valid'),
    )
    
    def calculate_proportional_discount(self, new_total: Decimal):
        """
        Distribute discount proportionally when total is changed.
        
        Example:
        - Original total: 3,500,000 so'm
        - New total: 3,000,000 so'm
        - Each item gets proportionally reduced
        
        This method should be called from service layer.
        """
        if self.subtotal == 0:
            return
        
        discount_ratio = Decimal(str(new_total)) / Decimal(str(self.subtotal))
        
        for item in self.items:
            original_item_total = item.original_price * item.quantity
            new_item_total = (original_item_total * discount_ratio).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            item.unit_price = (new_item_total / item.quantity).quantize(
                Decimal('0.0001'), rounding=ROUND_HALF_UP
            )
            item.total_price = new_item_total
            item.discount_percent = ((1 - discount_ratio) * 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            item.discount_amount = original_item_total - new_item_total
        
        self.total_amount = new_total
        self.discount_amount = self.subtotal - new_total
        self.discount_percent = ((self.discount_amount / self.subtotal) * 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )


class SaleItem(BaseModel):
    """
    Sale line item.
    
    Stores both original price and final price for reporting.
    """
    
    __tablename__ = 'sale_items'
    
    sale_id = Column(Integer, ForeignKey('sales.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Quantity and UOM
    quantity = Column(Numeric(20, 4), nullable=False)
    uom_id = Column(Integer, ForeignKey('units_of_measure.id'), nullable=False)
    base_quantity = Column(Numeric(20, 4), nullable=False)  # In product's base UOM
    
    # Pricing
    original_price = Column(Numeric(20, 4), nullable=False)  # Catalog price per unit
    unit_price = Column(Numeric(20, 4), nullable=False)  # Actual sale price per unit
    
    # Discount on this item
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(20, 4), default=0)
    
    # Totals
    total_price = Column(Numeric(20, 4), nullable=False)  # Final total for this line
    
    # Cost for profit calculation
    unit_cost = Column(Numeric(20, 4), default=0)  # Cost price at time of sale
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")
    uom = relationship("UnitOfMeasure")
    
    __table_args__ = (
        Index('ix_sale_items_sale_id', 'sale_id'),
        Index('ix_sale_items_product_id', 'product_id'),
        CheckConstraint('quantity > 0', name='ck_sale_item_positive_quantity'),
        CheckConstraint('unit_price >= 0', name='ck_sale_item_price_non_negative'),
    )
    
    @property
    def profit(self) -> Decimal:
        """Calculate profit for this line item."""
        return Decimal(str(self.total_price)) - (Decimal(str(self.unit_cost)) * Decimal(str(self.quantity)))
    
    @property
    def profit_margin(self) -> Decimal:
        """Calculate profit margin percentage."""
        if self.total_price == 0:
            return Decimal(0)
        return (self.profit / Decimal(str(self.total_price))) * 100


class Payment(BaseModel):
    """
    Payment transaction.
    
    A sale can have multiple payments (partial payments, mixed types).
    """
    
    __tablename__ = 'payments'
    
    # Reference number
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    payment_date = Column(Date, nullable=False)
    
    # Links
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=True)  # Can be debt payment without sale
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    
    # Payment details
    payment_type = Column(Enum(PaymentType), nullable=False)
    amount = Column(Numeric(20, 4), nullable=False)
    
    # For card/transfer payments
    transaction_id = Column(String(100), nullable=True)  # External transaction ID
    
    # Cash register
    cash_register_id = Column(Integer, ForeignKey('cash_registers.id'), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Status
    is_confirmed = Column(Boolean, default=True)
    is_cancelled = Column(Boolean, default=False)
    
    # Audit
    received_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    sale = relationship("Sale", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    cash_register = relationship("CashRegister")
    received_by = relationship("User")
    
    __table_args__ = (
        Index('ix_payments_sale_id', 'sale_id'),
        Index('ix_payments_customer_id', 'customer_id'),
        Index('ix_payments_payment_date', 'payment_date'),
        Index('ix_payments_payment_type', 'payment_type'),
        CheckConstraint('amount > 0', name='ck_payment_positive_amount'),
    )


class SaleReturn(BaseModel):
    """
    Customer return/refund transaction.
    """
    
    __tablename__ = 'sale_returns'
    
    # Reference
    return_number = Column(String(50), unique=True, nullable=False, index=True)
    return_date = Column(Date, nullable=False)
    
    # Original sale reference
    original_sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # Amounts
    total_amount = Column(Numeric(20, 4), nullable=False)
    refund_amount = Column(Numeric(20, 4), default=0)  # Cash refund
    credit_amount = Column(Numeric(20, 4), default=0)  # Applied to customer balance
    
    # Reason
    return_reason = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default='pending')  # pending, approved, completed, rejected
    
    # Stock handling
    restock_items = Column(Boolean, default=True)  # Return items to stock
    
    # Audit
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(String(50), nullable=True)
    
    # Relationships
    original_sale = relationship("Sale")
    customer = relationship("Customer")
    warehouse = relationship("Warehouse")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    items = relationship("SaleReturnItem", back_populates="sale_return", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_sale_returns_original_sale_id', 'original_sale_id'),
        Index('ix_sale_returns_customer_id', 'customer_id'),
        Index('ix_sale_returns_return_date', 'return_date'),
        Index('ix_sale_returns_status', 'status'),
    )


class SaleReturnItem(BaseModel):
    """
    Return line items.
    """
    
    __tablename__ = 'sale_return_items'
    
    sale_return_id = Column(Integer, ForeignKey('sale_returns.id', ondelete='CASCADE'), nullable=False)
    original_sale_item_id = Column(Integer, ForeignKey('sale_items.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Quantities
    quantity = Column(Numeric(20, 4), nullable=False)
    uom_id = Column(Integer, ForeignKey('units_of_measure.id'), nullable=False)
    base_quantity = Column(Numeric(20, 4), nullable=False)
    
    # Refund price (from original sale)
    unit_price = Column(Numeric(20, 4), nullable=False)
    total_price = Column(Numeric(20, 4), nullable=False)
    
    # Reason
    reason = Column(Text, nullable=True)
    condition = Column(String(50), default='good')  # good, damaged, defective
    
    # Relationships
    sale_return = relationship("SaleReturn", back_populates="items")
    original_sale_item = relationship("SaleItem")
    product = relationship("Product")
    uom = relationship("UnitOfMeasure")
    
    __table_args__ = (
        Index('ix_return_items_return_id', 'sale_return_id'),
        Index('ix_return_items_product_id', 'product_id'),
    )


class Receipt(BaseModel):
    """
    Receipt/Invoice storage.
    Stores generated receipt documents.
    """
    
    __tablename__ = 'receipts'
    
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False, unique=True)
    
    receipt_number = Column(String(50), unique=True, nullable=False)
    receipt_type = Column(String(20), default='sale')  # sale, return, invoice
    
    # Document storage
    document_url = Column(String(500), nullable=True)  # PDF/image URL
    document_data = Column(Text, nullable=True)  # JSON receipt data
    
    # Print tracking
    print_count = Column(Integer, default=0)
    last_printed_at = Column(String(50), nullable=True)
    
    # Relationships
    sale = relationship("Sale")
    
    __table_args__ = (
        Index('ix_receipts_sale_id', 'sale_id'),
        Index('ix_receipts_receipt_number', 'receipt_number'),
    )
