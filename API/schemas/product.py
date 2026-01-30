"""
Product, Category, and UOM schemas.
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, field_validator

from .base import BaseSchema, TimestampMixin


# ==================== UOM SCHEMAS ====================

class UOMBase(BaseSchema):
    """Base Unit of Measure schema."""
    
    name: str
    symbol: str
    description: Optional[str] = None
    uom_type: str  # weight, length, area, volume, piece
    base_factor: Decimal = Decimal("1")
    decimal_places: int = 2
    is_integer_only: bool = False


class UOMCreate(UOMBase):
    """Schema for creating a UOM."""
    pass


class UOMUpdate(BaseSchema):
    """Schema for updating a UOM."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    decimal_places: Optional[int] = None
    is_integer_only: Optional[bool] = None
    is_active: Optional[bool] = None


class UOMResponse(UOMBase, TimestampMixin):
    """UOM response schema."""
    
    id: int
    is_active: bool


class UOMListResponse(BaseModel):
    """UOM list response."""
    
    success: bool = True
    data: List[UOMResponse]
    count: int


# ==================== CATEGORY SCHEMAS ====================

class CategoryBase(BaseSchema):
    """Base category schema."""
    
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    
    slug: Optional[str] = None  # Auto-generated if not provided


class CategoryUpdate(BaseSchema):
    """Schema for updating a category."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase, TimestampMixin):
    """Category response schema."""
    
    id: int
    slug: str
    is_active: bool
    children_count: int = 0
    products_count: int = 0


class CategoryTreeResponse(CategoryResponse):
    """Category with children for tree view."""
    
    children: List["CategoryTreeResponse"] = []


class CategoryListResponse(BaseModel):
    """Category list response."""
    
    success: bool = True
    data: List[CategoryResponse]
    count: int


# ==================== PRODUCT UOM CONVERSION SCHEMAS ====================

class ProductUOMConversionBase(BaseSchema):
    """Base product UOM conversion schema."""
    
    uom_id: int
    conversion_factor: Decimal
    sale_price: Optional[Decimal] = None
    vip_price: Optional[Decimal] = None
    is_default_sale_uom: bool = False
    is_default_purchase_uom: bool = False
    is_integer_only: bool = False


class ProductUOMConversionCreate(ProductUOMConversionBase):
    """Schema for creating a product UOM conversion."""
    pass


class UniversalUOMConversionCreate(BaseSchema):
    """Schema for universal UOM conversion.
    
    Allows defining conversion between any two UOMs.
    Example: 1 tonna = 52 dona, 1 dona = 12 metr
    """
    from_uom_id: int      # Source UOM (must exist in product)
    to_uom_id: int        # Target UOM (new UOM to add)
    factor: Decimal       # How many target UOMs = 1 source UOM
    sale_price: Optional[Decimal] = None


class ProductUOMConversionResponse(ProductUOMConversionBase, TimestampMixin):
    """Product UOM conversion response."""
    
    id: int
    product_id: int
    uom: Optional[UOMResponse] = None


# ==================== PRODUCT SCHEMAS ====================

class ProductBase(BaseSchema):
    """Base product schema."""
    
    name: str
    article: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    base_uom_id: int
    cost_price: Decimal = Decimal("0")
    sale_price: Decimal = Decimal("0")
    sale_price_usd: Optional[Decimal] = None  # Sotish narxi USD
    vip_price: Optional[Decimal] = None
    vip_price_usd: Optional[Decimal] = None  # VIP narx USD
    color: Optional[str] = None  # HEX color (#FF5733)
    is_favorite: bool = False  # Tez-tez sotiladigan
    sort_order: int = 0  # Tartib
    min_stock_level: Decimal = Decimal("0")
    track_stock: bool = True
    allow_negative_stock: bool = False
    image_url: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    country_of_origin: Optional[str] = None
    is_featured: bool = False
    is_service: bool = False


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    
    uom_conversions: List[ProductUOMConversionCreate] = []
    
    @field_validator("barcode", "article", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        """Convert empty strings to None to avoid unique constraint issues."""
        if v == "" or v == "":
            return None
        return v
    
    @field_validator("cost_price", "sale_price")
    @classmethod
    def validate_prices(cls, v: Decimal) -> Decimal:
        """Validate prices are non-negative."""
        if v < 0:
            raise ValueError("Narx manfiy bo'lishi mumkin emas")
        return v


class ProductUpdate(BaseSchema):
    """Schema for updating a product."""
    
    name: Optional[str] = None
    article: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    base_uom_id: Optional[int] = None  # Asosiy o'lchov birligi
    cost_price: Optional[Decimal] = None
    sale_price: Optional[Decimal] = None
    sale_price_usd: Optional[Decimal] = None
    vip_price: Optional[Decimal] = None
    vip_price_usd: Optional[Decimal] = None
    color: Optional[str] = None
    is_favorite: Optional[bool] = None
    sort_order: Optional[int] = None
    min_stock_level: Optional[Decimal] = None
    track_stock: Optional[bool] = None
    allow_negative_stock: Optional[bool] = None
    image_url: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    country_of_origin: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None

    @field_validator("barcode", "article", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        """Convert empty strings to None to avoid unique constraint issues."""
        if v == "" or v == "":
            return None
        return v


class ProductResponse(ProductBase, TimestampMixin):
    """Product response schema."""

    id: int
    is_active: bool
    category: Optional[CategoryResponse] = None
    base_uom: Optional[UOMResponse] = None
    uom_conversions: List[ProductUOMConversionResponse] = []


class ProductListItem(BaseSchema):
    """Simplified product for lists."""

    id: int
    name: str
    article: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    base_uom_id: int
    base_uom_symbol: str
    base_uom_name: Optional[str] = None
    cost_price: Decimal
    cost_price_usd: Optional[float] = None
    sale_price: Decimal
    sale_price_usd: Optional[float] = None
    vip_price: Optional[Decimal] = None
    vip_price_usd: Optional[float] = None
    min_stock_level: Decimal = Decimal("0")
    color: Optional[str] = None
    is_favorite: bool = False
    sort_order: int = 0
    image_url: Optional[str] = None
    is_active: bool
    current_stock: Decimal = Decimal("0")
    uom_conversions: List[dict] = []

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Product list response with pagination."""

    success: bool = True
    data: List[ProductListItem]
    total: int
    page: int
    per_page: int


class ProductSearchParams(BaseModel):
    """Product search parameters."""

    q: Optional[str] = None  # Search query (name, article, barcode)
    category_id: Optional[int] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    in_stock: Optional[bool] = None  # Only products with stock > 0
    is_active: bool = True
    sort_by: str = "name"  # name, price, created_at
    sort_order: str = "asc"


class ProductStockInfo(BaseSchema):
    """Product stock information."""

    product_id: int
    product_name: str
    warehouse_id: int
    warehouse_name: str
    quantity: Decimal
    base_uom_symbol: str
    # Converted quantities
    quantities_by_uom: dict = {}  # {uom_symbol: quantity}
    average_cost: Decimal
    total_value: Decimal
    min_stock_level: Decimal
    is_below_minimum: bool


class BulkPriceUpdateRequest(BaseModel):
    """Bulk price update request."""

    product_ids: List[int]
    price_type: str  # cost, sale, vip
    adjustment_type: str  # percent, fixed
    adjustment_value: Decimal

    @field_validator("price_type")
    @classmethod
    def validate_price_type(cls, v: str) -> str:
        """Validate price type."""
        allowed = ["cost", "sale", "vip"]
        if v not in allowed:
            raise ValueError(f"Narx turi {allowed} dan biri bo'lishi kerak")
        return v