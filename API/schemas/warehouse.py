"""
Warehouse, Stock, and Inventory schemas.
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date
from pydantic import BaseModel, field_validator

from .base import BaseSchema, TimestampMixin


# ==================== WAREHOUSE SCHEMAS ====================

class WarehouseBase(BaseSchema):
    """Base warehouse schema."""
    
    name: str
    code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_main: bool = False
    allow_negative_stock: bool = False


class WarehouseCreate(WarehouseBase):
    """Schema for creating a warehouse."""
    
    manager_id: Optional[int] = None


class WarehouseUpdate(BaseSchema):
    """Schema for updating a warehouse."""
    
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_id: Optional[int] = None
    is_main: Optional[bool] = None
    allow_negative_stock: Optional[bool] = None
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase, TimestampMixin):
    """Warehouse response schema."""
    
    id: int
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    is_active: bool
    products_count: int = 0
    total_value: Decimal = Decimal("0")


class WarehouseListResponse(BaseModel):
    """Warehouse list response."""
    
    success: bool = True
    data: List[WarehouseResponse]
    count: int


# ==================== STOCK SCHEMAS ====================

class StockResponse(BaseSchema, TimestampMixin):
    """Stock level response."""
    
    id: int
    product_id: int
    product_name: str
    product_article: Optional[str] = None
    warehouse_id: int
    warehouse_name: str
    quantity: Decimal
    base_uom_symbol: str
    reserved_quantity: Decimal
    available_quantity: Decimal
    average_cost: Decimal
    last_purchase_cost: Decimal
    total_value: Decimal  # quantity * average_cost
    min_stock_level: Decimal
    is_below_minimum: bool


class StockListResponse(BaseModel):
    """Stock list response."""
    
    success: bool = True
    data: List[StockResponse]
    total: int
    page: int
    per_page: int
    # Summary
    total_value: Decimal = Decimal("0")
    below_minimum_count: int = 0


class StockSearchParams(BaseModel):
    """Stock search parameters."""
    
    q: Optional[str] = None  # Search by product name/article
    warehouse_id: Optional[int] = None
    category_id: Optional[int] = None
    below_minimum: Optional[bool] = None
    out_of_stock: Optional[bool] = None
    sort_by: str = "product_name"
    sort_order: str = "asc"


# ==================== STOCK MOVEMENT SCHEMAS ====================

class StockMovementCreate(BaseSchema):
    """Schema for creating a stock movement (manual adjustment)."""
    
    product_id: int
    warehouse_id: int
    movement_type: str  # ADJUSTMENT_PLUS, ADJUSTMENT_MINUS, WRITE_OFF, INTERNAL_USE
    quantity: Decimal
    uom_id: int
    unit_cost: Optional[Decimal] = None
    notes: Optional[str] = None
    document_number: Optional[str] = None
    
    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Decimal) -> Decimal:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Miqdor 0 dan katta bo'lishi kerak")
        return v
    
    @field_validator("movement_type")
    @classmethod
    def validate_movement_type(cls, v: str) -> str:
        """Validate movement type."""
        allowed = ["ADJUSTMENT_PLUS", "ADJUSTMENT_MINUS", "WRITE_OFF", "INTERNAL_USE"]
        if v.upper() not in allowed:
            raise ValueError(f"Harakat turi {allowed} dan biri bo'lishi kerak")
        return v.upper()


class StockMovementResponse(BaseSchema, TimestampMixin):
    """Stock movement response schema."""
    
    id: int
    product_id: int
    product_name: str
    warehouse_id: int
    warehouse_name: str
    movement_type: str
    quantity: Decimal
    uom_id: int
    uom_symbol: str
    base_quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    stock_before: Decimal
    stock_after: Decimal
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    document_number: Optional[str] = None
    notes: Optional[str] = None
    created_by_id: int
    created_by_name: str
    approved_by_id: Optional[int] = None
    approved_by_name: Optional[str] = None


class StockMovementListResponse(BaseModel):
    """Stock movement list response."""
    
    success: bool = True
    data: List[StockMovementResponse]
    total: int
    page: int
    per_page: int


class StockMovementSearchParams(BaseModel):
    """Stock movement search parameters."""
    
    product_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    movement_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_by_id: Optional[int] = None


# ==================== STOCK INCOME (PURCHASE) SCHEMAS ====================

class StockIncomeItemCreate(BaseSchema):
    """Schema for stock income item."""
    
    product_id: int
    quantity: Decimal
    uom_id: int
    unit_price: Decimal  # Purchase price in UZS
    unit_price_usd: Optional[Decimal] = None  # Purchase price in USD
    exchange_rate: Optional[Decimal] = None  # Exchange rate at time of purchase
    
    @field_validator("quantity", "unit_price")
    @classmethod
    def validate_positive(cls, v: Decimal) -> Decimal:
        """Validate positive values."""
        if v <= 0:
            raise ValueError("Qiymat 0 dan katta bo'lishi kerak")
        return v


class StockIncomeCreate(BaseSchema):
    """Schema for creating stock income (kirim)."""
    
    warehouse_id: int
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None  # Supplier name (if not linked)
    items: List[StockIncomeItemCreate]
    document_number: Optional[str] = None  # Supplier invoice number
    document_date: Optional[date] = None
    exchange_rate: Optional[Decimal] = None  # USD exchange rate
    notes: Optional[str] = None
    
    @field_validator("items")
    @classmethod
    def validate_items(cls, v: List[StockIncomeItemCreate]) -> List[StockIncomeItemCreate]:
        """Validate at least one item."""
        if not v:
            raise ValueError("Kamida bitta tovar bo'lishi kerak")
        return v


# ==================== INVENTORY CHECK SCHEMAS ====================

class InventoryCheckItemCreate(BaseSchema):
    """Schema for inventory check item."""
    
    product_id: int
    actual_quantity: Decimal  # Counted quantity


class InventoryCheckCreate(BaseSchema):
    """Schema for creating an inventory check."""
    
    warehouse_id: int
    category_id: Optional[int] = None  # Optional category filter
    notes: Optional[str] = None


class InventoryCheckItemResponse(BaseSchema):
    """Inventory check item response."""
    
    id: int
    product_id: int
    product_name: str
    product_article: Optional[str] = None
    base_uom_symbol: str
    system_quantity: Decimal  # Expected from system
    actual_quantity: Optional[Decimal] = None  # Counted
    difference: Decimal
    unit_cost: Decimal
    difference_value: Decimal
    is_counted: bool
    counted_by_name: Optional[str] = None
    notes: Optional[str] = None


class InventoryCheckResponse(BaseSchema, TimestampMixin):
    """Inventory check response schema."""
    
    id: int
    check_number: str
    check_date: date
    warehouse_id: int
    warehouse_name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    status: str
    total_items_checked: int
    items_with_difference: int
    total_surplus_value: Decimal
    total_shortage_value: Decimal
    created_by_id: int
    created_by_name: str
    completed_by_id: Optional[int] = None
    completed_by_name: Optional[str] = None
    notes: Optional[str] = None
    items: List[InventoryCheckItemResponse] = []


class InventoryCheckUpdateItem(BaseSchema):
    """Schema for updating inventory check item."""
    
    item_id: int
    actual_quantity: Decimal
    notes: Optional[str] = None


class InventoryCheckComplete(BaseSchema):
    """Schema for completing inventory check."""
    
    apply_adjustments: bool = True  # Create stock adjustments for differences


# ==================== STOCK TRANSFER SCHEMAS ====================

class StockTransferItemCreate(BaseSchema):
    """Schema for stock transfer item."""
    
    product_id: int
    quantity: Decimal
    uom_id: int
    notes: Optional[str] = None
    
    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Decimal) -> Decimal:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Miqdor 0 dan katta bo'lishi kerak")
        return v


class StockTransferCreate(BaseSchema):
    """Schema for creating a stock transfer."""
    
    from_warehouse_id: int
    to_warehouse_id: int
    items: List[StockTransferItemCreate]
    notes: Optional[str] = None
    
    @field_validator("items")
    @classmethod
    def validate_items(cls, v: List[StockTransferItemCreate]) -> List[StockTransferItemCreate]:
        """Validate at least one item."""
        if not v:
            raise ValueError("Kamida bitta tovar bo'lishi kerak")
        return v


class StockTransferResponse(BaseSchema, TimestampMixin):
    """Stock transfer response schema."""
    
    id: int
    transfer_number: str
    transfer_date: date
    from_warehouse_id: int
    from_warehouse_name: str
    to_warehouse_id: int
    to_warehouse_name: str
    status: str
    items_count: int
    created_by_id: int
    created_by_name: str
    received_by_id: Optional[int] = None
    received_by_name: Optional[str] = None
    notes: Optional[str] = None


class StockTransferReceive(BaseSchema):
    """Schema for receiving a stock transfer."""
    
    items: List[dict]  # [{item_id: int, received_quantity: Decimal}]
    notes: Optional[str] = None
