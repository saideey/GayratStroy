"""
Sale, Payment, and related schemas.
Supports proportional discount distribution.
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date
from pydantic import BaseModel, field_validator

from .base import BaseSchema, TimestampMixin


# ==================== SALE ITEM SCHEMAS ====================

class SaleItemCreate(BaseSchema):
    """Schema for creating a sale item."""
    
    product_id: int
    quantity: Decimal
    uom_id: int
    unit_price: Optional[Decimal] = None  # If None, use catalog price
    original_price: Optional[Decimal] = None  # Original catalog price before discount
    discount_percent: Optional[Decimal] = Decimal("0")
    discount_amount: Optional[Decimal] = Decimal("0")
    notes: Optional[str] = None
    
    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Decimal) -> Decimal:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Miqdor 0 dan katta bo'lishi kerak")
        return v


class SaleItemResponse(BaseSchema, TimestampMixin):
    """Sale item response schema."""
    
    id: int
    product_id: int
    product_name: str
    product_article: Optional[str] = None
    quantity: Decimal
    uom_id: int
    uom_symbol: str
    base_quantity: Decimal
    original_price: Decimal  # Catalog price
    unit_price: Decimal  # Actual sale price
    discount_percent: Decimal
    discount_amount: Decimal
    total_price: Decimal
    unit_cost: Decimal
    notes: Optional[str] = None


# ==================== PAYMENT SCHEMAS ====================

class PaymentCreate(BaseSchema):
    """Schema for creating a payment."""
    
    payment_type: str  # CASH, CARD, TRANSFER
    amount: Decimal
    transaction_id: Optional[str] = None  # For card/transfer
    notes: Optional[str] = None
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate payment amount."""
        if v <= 0:
            raise ValueError("To'lov summasi 0 dan katta bo'lishi kerak")
        return v
    
    @field_validator("payment_type")
    @classmethod
    def validate_payment_type(cls, v: str) -> str:
        """Validate payment type."""
        allowed = ["CASH", "CARD", "TRANSFER", "DEBT", "MIXED"]
        if v.upper() not in allowed:
            raise ValueError(f"To'lov turi {allowed} dan biri bo'lishi kerak")
        return v.upper()


class PaymentResponse(BaseSchema, TimestampMixin):
    """Payment response schema."""
    
    id: int
    payment_number: str
    payment_date: date
    sale_id: Optional[int] = None
    customer_id: Optional[int] = None
    payment_type: str
    amount: Decimal
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    is_confirmed: bool
    is_cancelled: bool
    received_by_id: int
    received_by_name: Optional[str] = None


# ==================== SALE SCHEMAS ====================

class SaleCreate(BaseSchema):
    """
    Schema for creating a sale.
    
    Key feature: If final_total is provided and differs from calculated total,
    system will distribute discount proportionally across all items.
    """
    
    customer_id: Optional[int] = None
    warehouse_id: int
    items: List[SaleItemCreate]
    
    # Optional: Override total (triggers proportional discount)
    final_total: Optional[Decimal] = None
    
    # Payments (can be multiple for mixed payment)
    payments: List[PaymentCreate] = []
    
    # Additional info
    notes: Optional[str] = None
    requires_delivery: bool = False
    delivery_address: Optional[str] = None
    delivery_date: Optional[date] = None
    delivery_cost: Decimal = Decimal("0")
    
    @field_validator("items")
    @classmethod
    def validate_items(cls, v: List[SaleItemCreate]) -> List[SaleItemCreate]:
        """Validate at least one item."""
        if not v:
            raise ValueError("Kamida bitta tovar bo'lishi kerak")
        return v


class SaleResponse(BaseSchema, TimestampMixin):
    """Full sale response schema."""
    
    id: int
    sale_number: str
    sale_date: date
    
    # Customer info
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    
    # Seller info
    seller_id: int
    seller_name: str
    
    # Warehouse
    warehouse_id: int
    warehouse_name: str
    
    # Amounts
    subtotal: Decimal  # Before discount
    discount_amount: Decimal
    discount_percent: Decimal
    total_amount: Decimal  # After discount
    paid_amount: Decimal
    debt_amount: Decimal
    
    # Status
    payment_status: str
    payment_type: Optional[str] = None
    
    # Items and payments
    items: List[SaleItemResponse] = []
    payments: List[PaymentResponse] = []
    
    # Delivery
    requires_delivery: bool
    delivery_address: Optional[str] = None
    delivery_date: Optional[date] = None
    delivery_cost: Decimal
    
    # Flags
    is_vip_sale: bool
    is_wholesale: bool
    is_cancelled: bool
    cancelled_reason: Optional[str] = None
    sms_sent: bool
    
    # Notes
    notes: Optional[str] = None


class SaleListItem(BaseSchema):
    """Simplified sale for lists."""
    
    id: int
    sale_number: str
    sale_date: date
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    seller_name: str
    total_amount: Decimal
    paid_amount: Decimal
    debt_amount: Decimal
    payment_status: str
    items_count: int
    is_cancelled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SaleListResponse(BaseModel):
    """Sale list response with pagination."""
    
    success: bool = True
    data: List[SaleListItem]
    total: int
    page: int
    per_page: int
    # Summary
    total_amount_sum: Decimal = Decimal("0")
    total_paid_sum: Decimal = Decimal("0")
    total_debt_sum: Decimal = Decimal("0")


class SaleSearchParams(BaseModel):
    """Sale search parameters."""
    
    q: Optional[str] = None  # Search by sale number
    customer_id: Optional[int] = None
    seller_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    payment_status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    has_debt: Optional[bool] = None
    is_cancelled: bool = False
    sort_by: str = "created_at"
    sort_order: str = "desc"


class SaleCancelRequest(BaseModel):
    """Sale cancellation request."""
    
    reason: str
    return_to_stock: bool = True  # Return items to stock


class QuickSaleRequest(BaseSchema):
    """
    Quick sale request for POS.
    Simplified version for fast checkout.
    """
    
    items: List[SaleItemCreate]
    customer_id: Optional[int] = None
    warehouse_id: int
    
    # Final amount (optional - for manual total override)
    final_total: Optional[Decimal] = None
    
    # Single payment (for quick checkout)
    payment_type: str = "CASH"
    payment_amount: Decimal
    
    notes: Optional[str] = None


class SaleReceiptResponse(BaseModel):
    """Receipt data for printing."""
    
    sale_number: str
    sale_date: datetime
    
    # Company info
    company_name: str
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    
    # Customer
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    
    # Seller
    seller_name: str
    
    # Items
    items: List[dict]  # Simplified item format for receipt
    
    # Totals
    subtotal: Decimal
    discount_amount: Decimal
    discount_percent: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    debt_amount: Decimal
    change_amount: Decimal  # Qaytim (if overpaid)
    
    # Payment info
    payment_type: str
    
    # Footer
    thank_you_message: str = "Xaridingiz uchun rahmat!"


# ==================== RETURN SCHEMAS ====================

class SaleReturnItemCreate(BaseSchema):
    """Schema for creating a return item."""
    
    original_sale_item_id: int
    quantity: Decimal
    reason: Optional[str] = None
    condition: str = "good"  # good, damaged, defective
    
    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Decimal) -> Decimal:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Qaytarish miqdori 0 dan katta bo'lishi kerak")
        return v


class SaleReturnCreate(BaseSchema):
    """Schema for creating a sale return."""
    
    original_sale_id: int
    items: List[SaleReturnItemCreate]
    return_reason: Optional[str] = None
    restock_items: bool = True


class SaleReturnResponse(BaseSchema, TimestampMixin):
    """Sale return response schema."""
    
    id: int
    return_number: str
    return_date: date
    original_sale_id: int
    original_sale_number: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    warehouse_id: int
    total_amount: Decimal
    refund_amount: Decimal
    credit_amount: Decimal
    return_reason: Optional[str] = None
    status: str
    restock_items: bool
