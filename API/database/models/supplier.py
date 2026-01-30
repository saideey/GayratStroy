"""
Supplier and Purchase Order models.
Handles supplier management and stock receipts.
"""

from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Numeric, Date,
    ForeignKey, Enum, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from ..base import BaseModel, SoftDeleteMixin


class Supplier(BaseModel, SoftDeleteMixin):
    """
    Supplier/Vendor model.
    
    Tracks suppliers for purchase management.
    """
    
    __tablename__ = 'suppliers'
    
    # Basic info
    name = Column(String(300), nullable=False, index=True)
    company_name = Column(String(300), nullable=True)
    contact_person = Column(String(200), nullable=True)
    
    # Contact
    phone = Column(String(20), nullable=True, index=True)
    phone_secondary = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Address
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Legal info
    inn = Column(String(50), nullable=True)  # INN (tax ID)
    bank_account = Column(String(100), nullable=True)
    bank_name = Column(String(200), nullable=True)
    mfo = Column(String(20), nullable=True)  # Bank MFO
    
    # Financial
    credit_days = Column(Integer, default=0)  # Payment terms
    current_debt = Column(Numeric(20, 4), default=0)  # What we owe them
    advance_balance = Column(Numeric(20, 4), default=0)  # Prepaid amount
    
    # Categories they supply
    product_categories = Column(Text, nullable=True)  # JSON array of category IDs
    
    # Rating
    rating = Column(Integer, default=5)  # 1-5 stars
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier", lazy="dynamic")
    
    __table_args__ = (
        Index('ix_suppliers_is_active', 'is_active'),
    )


class PurchaseOrderStatus(PyEnum):
    """Purchase order statuses."""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    ORDERED = "ordered"  # Order sent to supplier
    PARTIAL = "partial"  # Partially received
    RECEIVED = "received"  # Fully received
    CANCELLED = "cancelled"


class PurchaseOrder(BaseModel):
    """
    Purchase order for stock receipt.
    
    Used for:
    - Creating purchase orders to suppliers
    - Recording received goods
    - Tracking supplier payments
    """
    
    __tablename__ = 'purchase_orders'
    
    # Reference
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    order_date = Column(Date, nullable=False)
    
    # Parties
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # External reference
    supplier_invoice = Column(String(100), nullable=True)  # Supplier's invoice number
    supplier_invoice_date = Column(Date, nullable=True)
    
    # Status
    status = Column(Enum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT, nullable=False)
    
    # Amounts
    subtotal = Column(Numeric(20, 4), default=0)  # Before additional costs
    shipping_cost = Column(Numeric(20, 4), default=0)
    other_costs = Column(Numeric(20, 4), default=0)
    tax_amount = Column(Numeric(20, 4), default=0)
    total_amount = Column(Numeric(20, 4), nullable=False)
    
    # Payment
    paid_amount = Column(Numeric(20, 4), default=0)
    payment_status = Column(String(20), default='unpaid')  # unpaid, partial, paid
    payment_due_date = Column(Date, nullable=True)
    
    # Dates
    expected_date = Column(Date, nullable=True)  # Expected delivery date
    received_date = Column(Date, nullable=True)  # Actual received date
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(String(50), nullable=True)
    received_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    warehouse = relationship("Warehouse")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    received_by = relationship("User", foreign_keys=[received_by_id])
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", lazy="dynamic", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_purchase_orders_supplier_id', 'supplier_id'),
        Index('ix_purchase_orders_warehouse_id', 'warehouse_id'),
        Index('ix_purchase_orders_status', 'status'),
        Index('ix_purchase_orders_order_date', 'order_date'),
        CheckConstraint('total_amount >= 0', name='ck_po_total_non_negative'),
    )


class PurchaseOrderItem(BaseModel):
    """
    Purchase order line items.
    """
    
    __tablename__ = 'purchase_order_items'
    
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Ordered quantity
    ordered_quantity = Column(Numeric(20, 4), nullable=False)
    uom_id = Column(Integer, ForeignKey('units_of_measure.id'), nullable=False)
    base_ordered_quantity = Column(Numeric(20, 4), nullable=False)  # In base UOM
    
    # Received quantity (may differ from ordered)
    received_quantity = Column(Numeric(20, 4), default=0)
    base_received_quantity = Column(Numeric(20, 4), default=0)
    
    # Pricing
    unit_price = Column(Numeric(20, 4), nullable=False)
    total_price = Column(Numeric(20, 4), nullable=False)
    
    # Tax
    tax_percent = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(20, 4), default=0)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
    uom = relationship("UnitOfMeasure")
    
    __table_args__ = (
        Index('ix_po_items_order_id', 'purchase_order_id'),
        Index('ix_po_items_product_id', 'product_id'),
        CheckConstraint('ordered_quantity > 0', name='ck_po_item_positive_quantity'),
        CheckConstraint('unit_price >= 0', name='ck_po_item_price_non_negative'),
    )


class SupplierPayment(BaseModel):
    """
    Payment to supplier.
    """
    
    __tablename__ = 'supplier_payments'
    
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    payment_date = Column(Date, nullable=False)
    
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=True)
    
    # Payment details
    payment_type = Column(String(20), nullable=False)  # cash, transfer, card
    amount = Column(Numeric(20, 4), nullable=False)
    
    # Bank transfer details
    transaction_id = Column(String(100), nullable=True)
    bank_reference = Column(String(100), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    supplier = relationship("Supplier")
    purchase_order = relationship("PurchaseOrder")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    __table_args__ = (
        Index('ix_supplier_payments_supplier_id', 'supplier_id'),
        Index('ix_supplier_payments_order_id', 'purchase_order_id'),
        Index('ix_supplier_payments_date', 'payment_date'),
        CheckConstraint('amount > 0', name='ck_supplier_payment_positive'),
    )


class SupplierPriceList(BaseModel):
    """
    Supplier price list for comparison.
    Track historical prices from suppliers.
    """
    
    __tablename__ = 'supplier_price_lists'
    
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Price details
    price = Column(Numeric(20, 4), nullable=False)
    uom_id = Column(Integer, ForeignKey('units_of_measure.id'), nullable=False)
    min_quantity = Column(Numeric(20, 4), default=0)  # Minimum order quantity
    
    # Validity
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    supplier = relationship("Supplier")
    product = relationship("Product")
    uom = relationship("UnitOfMeasure")
    
    __table_args__ = (
        Index('ix_supplier_prices_supplier_id', 'supplier_id'),
        Index('ix_supplier_prices_product_id', 'product_id'),
        CheckConstraint('price >= 0', name='ck_supplier_price_non_negative'),
    )
