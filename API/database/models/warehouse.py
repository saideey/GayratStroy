"""
Warehouse, Stock, and Inventory models.
Handles stock tracking, movements, and inventory management.
"""

from enum import Enum as PyEnum
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Numeric, Date,
    ForeignKey, Enum, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship

from ..base import BaseModel, SoftDeleteMixin


class Warehouse(BaseModel, SoftDeleteMixin):
    """
    Warehouse/Store location model.
    
    Supports multiple warehouses/branches.
    """
    
    __tablename__ = 'warehouses'
    
    name = Column(String(200), nullable=False, unique=True)
    code = Column(String(50), nullable=True, unique=True)  # Short code like WH-01
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Manager
    manager_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_main = Column(Boolean, default=False)  # Main warehouse flag
    allow_negative_stock = Column(Boolean, default=False)
    
    # Relationships
    manager = relationship("User", foreign_keys=[manager_id])
    stock_items = relationship("Stock", back_populates="warehouse", lazy="dynamic")
    
    __table_args__ = (
        Index('ix_warehouses_is_active', 'is_active'),
    )


class Stock(BaseModel):
    """
    Current stock levels for products in warehouses.
    
    Quantity is always stored in product's base UOM.
    Real-time updates on sales/purchases.
    """
    
    __tablename__ = 'stock'
    
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # Quantities in base UOM
    quantity = Column(Numeric(20, 4), default=0, nullable=False)  # Current stock
    reserved_quantity = Column(Numeric(20, 4), default=0, nullable=False)  # Reserved for orders
    
    # Cost tracking (for FIFO/weighted average)
    average_cost = Column(Numeric(20, 4), default=0, nullable=False)  # Weighted average cost
    last_purchase_cost = Column(Numeric(20, 4), default=0, nullable=False)  # Last purchase price in UZS
    last_purchase_cost_usd = Column(Numeric(20, 4), nullable=True)  # Last purchase price in USD
    
    # Timestamps
    last_stock_update = Column(String(50), nullable=True)
    last_inventory_date = Column(Date, nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="stock_items")
    warehouse = relationship("Warehouse", back_populates="stock_items")
    
    __table_args__ = (
        UniqueConstraint('product_id', 'warehouse_id', name='uq_stock_product_warehouse'),
        Index('ix_stock_product_id', 'product_id'),
        Index('ix_stock_warehouse_id', 'warehouse_id'),
        Index('ix_stock_quantity', 'quantity'),
    )
    
    @property
    def available_quantity(self) -> Decimal:
        """Get available quantity (total - reserved)."""
        return Decimal(str(self.quantity)) - Decimal(str(self.reserved_quantity))
    
    def is_below_minimum(self, min_level: Decimal) -> bool:
        """Check if stock is below minimum level."""
        return self.quantity < min_level


class MovementType(PyEnum):
    """Types of stock movements."""
    PURCHASE = "purchase"  # Kirim (postavshchikdan)
    SALE = "sale"  # Chiqim (sotuvdan)
    TRANSFER_IN = "transfer_in"  # Boshqa ombordan kelish
    TRANSFER_OUT = "transfer_out"  # Boshqa omborga jo'natish
    ADJUSTMENT_PLUS = "adjustment_plus"  # Inventarizatsiya ortiqcha
    ADJUSTMENT_MINUS = "adjustment_minus"  # Inventarizatsiya kamomad
    RETURN_FROM_CUSTOMER = "return_from_customer"  # Mijozdan qaytarish
    RETURN_TO_SUPPLIER = "return_to_supplier"  # Yetkazib beruvchiga qaytarish
    WRITE_OFF = "write_off"  # Zarar / spisaniye
    INTERNAL_USE = "internal_use"  # Ichki ehtiyoj


class StockMovement(BaseModel):
    """
    Stock movement/transaction log.
    
    Records all stock changes with full audit trail.
    """
    
    __tablename__ = 'stock_movements'
    
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # Movement details
    movement_type = Column(Enum(MovementType), nullable=False)
    
    # Quantities
    quantity = Column(Numeric(20, 4), nullable=False)  # Always positive
    uom_id = Column(Integer, ForeignKey('units_of_measure.id'), nullable=False)  # UOM used in document
    base_quantity = Column(Numeric(20, 4), nullable=False)  # Converted to base UOM
    
    # Cost tracking
    unit_cost = Column(Numeric(20, 4), default=0)  # Cost per unit (in used UOM)
    total_cost = Column(Numeric(20, 4), default=0)  # Total cost
    
    # Balance after movement
    stock_before = Column(Numeric(20, 4), nullable=False)
    stock_after = Column(Numeric(20, 4), nullable=False)
    
    # Reference to source document
    reference_type = Column(String(50), nullable=True)  # purchase_order, sale, transfer, etc.
    reference_id = Column(Integer, nullable=True)
    
    # Transfer specific
    related_warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=True)  # For transfers
    
    # Additional info
    document_number = Column(String(100), nullable=True)  # External document number
    notes = Column(Text, nullable=True)
    
    # Supplier info (for purchases)
    supplier_name = Column(String(200), nullable=True)
    
    # USD pricing
    unit_price_usd = Column(Numeric(20, 4), nullable=True)  # Price in USD
    exchange_rate = Column(Numeric(20, 4), nullable=True)  # USD rate at time of transaction
    
    # Audit
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(String(50), nullable=True)
    
    # Edit tracking
    updated_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Delete tracking (soft delete)
    is_deleted = Column(Boolean, default=False)
    deleted_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    deleted_at = Column(String(50), nullable=True)
    deleted_reason = Column(Text, nullable=True)
    
    # Relationships
    product = relationship("Product")
    warehouse = relationship("Warehouse", foreign_keys=[warehouse_id])
    related_warehouse = relationship("Warehouse", foreign_keys=[related_warehouse_id])
    uom = relationship("UnitOfMeasure")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
    
    __table_args__ = (
        Index('ix_stock_movements_product_id', 'product_id'),
        Index('ix_stock_movements_warehouse_id', 'warehouse_id'),
        Index('ix_stock_movements_type', 'movement_type'),
        Index('ix_stock_movements_reference', 'reference_type', 'reference_id'),
        Index('ix_stock_movements_created_at', 'created_at'),
        CheckConstraint('quantity > 0', name='ck_movement_positive_quantity'),
    )


class InventoryCheckStatus(PyEnum):
    """Inventory check statuses."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InventoryCheck(BaseModel):
    """
    Inventory check/count header.
    
    Used for periodic stock verification (inventarizatsiya).
    """
    
    __tablename__ = 'inventory_checks'
    
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # Check info
    check_number = Column(String(50), unique=True, nullable=False)
    check_date = Column(Date, nullable=False)
    status = Column(Enum(InventoryCheckStatus), default=InventoryCheckStatus.DRAFT, nullable=False)
    
    # Category filter (optional - check specific category only)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    completed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    completed_at = Column(String(50), nullable=True)
    
    # Summary (updated on completion)
    total_items_checked = Column(Integer, default=0)
    items_with_difference = Column(Integer, default=0)
    total_surplus_value = Column(Numeric(20, 4), default=0)  # Ortiqcha summasi
    total_shortage_value = Column(Numeric(20, 4), default=0)  # Kamomad summasi
    
    # Relationships
    warehouse = relationship("Warehouse")
    category = relationship("Category")
    created_by = relationship("User", foreign_keys=[created_by_id])
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    items = relationship("InventoryCheckItem", back_populates="inventory_check", lazy="dynamic", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_inventory_checks_warehouse_id', 'warehouse_id'),
        Index('ix_inventory_checks_status', 'status'),
        Index('ix_inventory_checks_check_date', 'check_date'),
    )


class InventoryCheckItem(BaseModel):
    """
    Inventory check line items.
    
    Records expected vs actual quantities for each product.
    """
    
    __tablename__ = 'inventory_check_items'
    
    inventory_check_id = Column(Integer, ForeignKey('inventory_checks.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Quantities (in base UOM)
    system_quantity = Column(Numeric(20, 4), nullable=False)  # Expected (from system)
    actual_quantity = Column(Numeric(20, 4), nullable=True)  # Counted quantity
    difference = Column(Numeric(20, 4), default=0)  # actual - system
    
    # Cost impact
    unit_cost = Column(Numeric(20, 4), default=0)  # Cost per unit for valuation
    difference_value = Column(Numeric(20, 4), default=0)  # Monetary value of difference
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Status
    is_counted = Column(Boolean, default=False)
    counted_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    counted_at = Column(String(50), nullable=True)
    
    # Relationships
    inventory_check = relationship("InventoryCheck", back_populates="items")
    product = relationship("Product")
    counted_by = relationship("User")
    
    __table_args__ = (
        UniqueConstraint('inventory_check_id', 'product_id', name='uq_inventory_item'),
        Index('ix_inventory_items_check_id', 'inventory_check_id'),
        Index('ix_inventory_items_product_id', 'product_id'),
    )


class StockTransfer(BaseModel):
    """
    Stock transfer between warehouses.
    """
    
    __tablename__ = 'stock_transfers'
    
    transfer_number = Column(String(50), unique=True, nullable=False)
    transfer_date = Column(Date, nullable=False)
    
    # Warehouses
    from_warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    to_warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # Status
    status = Column(String(20), default='pending')  # pending, in_transit, completed, cancelled
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    received_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    received_at = Column(String(50), nullable=True)
    
    # Relationships
    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id])
    to_warehouse = relationship("Warehouse", foreign_keys=[to_warehouse_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    received_by = relationship("User", foreign_keys=[received_by_id])
    items = relationship("StockTransferItem", back_populates="transfer", lazy="dynamic", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_stock_transfers_from', 'from_warehouse_id'),
        Index('ix_stock_transfers_to', 'to_warehouse_id'),
        Index('ix_stock_transfers_status', 'status'),
        CheckConstraint('from_warehouse_id != to_warehouse_id', name='ck_transfer_different_warehouses'),
    )


class StockTransferItem(BaseModel):
    """
    Stock transfer line items.
    """
    
    __tablename__ = 'stock_transfer_items'
    
    transfer_id = Column(Integer, ForeignKey('stock_transfers.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Quantities
    quantity = Column(Numeric(20, 4), nullable=False)
    uom_id = Column(Integer, ForeignKey('units_of_measure.id'), nullable=False)
    base_quantity = Column(Numeric(20, 4), nullable=False)
    
    # Received quantity (may differ from sent)
    received_quantity = Column(Numeric(20, 4), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    transfer = relationship("StockTransfer", back_populates="items")
    product = relationship("Product")
    uom = relationship("UnitOfMeasure")
    
    __table_args__ = (
        Index('ix_transfer_items_transfer_id', 'transfer_id'),
        Index('ix_transfer_items_product_id', 'product_id'),
        CheckConstraint('quantity > 0', name='ck_transfer_item_positive_quantity'),
    )
