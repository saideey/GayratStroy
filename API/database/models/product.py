"""
Product, Category, and Unit of Measure (UOM) models.
Supports multiple units of measure per product with conversion factors.
"""

from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Numeric,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship

from ..base import BaseModel, SoftDeleteMixin


class Category(BaseModel, SoftDeleteMixin):
    """
    Product category with hierarchical structure.
    
    Example hierarchy:
    - Tsement
      - Tsement 400
      - Tsement 500
    - Armatura
      - Armatura 8mm
      - Armatura 10mm
    """
    
    __tablename__ = 'categories'
    
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    image_url = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    parent = relationship("Category", remote_side="Category.id", backref="children")
    products = relationship("Product", back_populates="category", lazy="dynamic")
    
    __table_args__ = (
        Index('ix_categories_parent_id', 'parent_id'),
        Index('ix_categories_is_active', 'is_active'),
        UniqueConstraint('name', 'parent_id', name='uq_category_name_parent'),
    )
    
    @property
    def full_path(self) -> str:
        """Get full category path (e.g., 'Tsement / Tsement 400')."""
        if self.parent:
            return f"{self.parent.full_path} / {self.name}"
        return self.name


class UnitOfMeasure(BaseModel):
    """
    Unit of Measure (UOM) definitions.
    
    Global units like kg, tonna, dona, metr, m², litr.
    These are shared across all products.
    """
    
    __tablename__ = 'units_of_measure'
    
    name = Column(String(100), nullable=False, unique=True)  # kilogramm, tonna, dona
    symbol = Column(String(20), nullable=False, unique=True)  # kg, t, dona
    description = Column(String(255), nullable=True)
    
    # Type categorization
    uom_type = Column(String(50), nullable=False)  # weight, length, area, volume, piece
    
    # Global conversion to base unit of same type
    # e.g., for weight: kg is base (factor=1), tonna has factor=1000
    base_factor = Column(Numeric(20, 10), default=1, nullable=False)
    
    # Display settings
    decimal_places = Column(Integer, default=2)  # How many decimals to show
    is_integer_only = Column(Boolean, default=False)  # e.g., dona must be integer
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index('ix_uom_type', 'uom_type'),
        CheckConstraint('base_factor > 0', name='ck_uom_positive_factor'),
    )


class Product(BaseModel, SoftDeleteMixin):
    """
    Product model with support for multiple units of measure.
    
    Key features:
    - Multiple UOMs with conversion factors
    - Three price levels: cost, sale, VIP
    - Stock tracking in base UOM
    - Minimum stock alerts
    """
    
    __tablename__ = 'products'
    
    # Basic info
    name = Column(String(300), nullable=False, index=True)
    article = Column(String(100), nullable=True, unique=True, index=True)  # SKU/Artikul
    barcode = Column(String(100), nullable=True, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Category
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    
    # Base unit of measure (all stock calculations in this unit)
    base_uom_id = Column(Integer, ForeignKey('units_of_measure.id'), nullable=False)
    
    # Pricing (in base UOM) - USD prices, UZS calculated from exchange rate
    cost_price = Column(Numeric(20, 4), default=0, nullable=False)  # Kelish narxi (себестоимость) UZS
    sale_price = Column(Numeric(20, 4), default=0, nullable=False)  # Sotish narxi UZS (legacy/calculated)
    sale_price_usd = Column(Numeric(20, 4), nullable=True)  # Sotish narxi USD
    vip_price = Column(Numeric(20, 4), nullable=True)  # VIP narx UZS
    vip_price_usd = Column(Numeric(20, 4), nullable=True)  # VIP narx USD
    
    # Display settings
    color = Column(String(7), nullable=True)  # HEX color code (e.g., #FF5733)
    is_favorite = Column(Boolean, default=False)  # Tez-tez sotiladigan
    sort_order = Column(Integer, default=0)  # Tartib raqami
    
    # Stock settings
    min_stock_level = Column(Numeric(20, 4), default=0)  # Minimal qoldiq chegarasi
    track_stock = Column(Boolean, default=True)  # Qoldiqni kuzatish
    allow_negative_stock = Column(Boolean, default=False)  # Manfiy qoldiqqa ruxsat
    
    # Media
    image_url = Column(String(500), nullable=True)
    images = Column(Text, nullable=True)  # JSON array of image URLs
    
    # Additional info
    brand = Column(String(100), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    country_of_origin = Column(String(100), nullable=True)
    
    # Flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False)  # Maxsus tovar
    is_service = Column(Boolean, default=False)  # Xizmat (qoldiqsiz)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    base_uom = relationship("UnitOfMeasure")
    uom_conversions = relationship("ProductUOMConversion", back_populates="product", lazy="dynamic", cascade="all, delete-orphan")
    stock_items = relationship("Stock", back_populates="product", lazy="dynamic")
    
    __table_args__ = (
        Index('ix_products_category_id', 'category_id'),
        Index('ix_products_base_uom_id', 'base_uom_id'),
        Index('ix_products_is_active', 'is_active'),
        Index('ix_products_name_search', 'name'),
        CheckConstraint('cost_price >= 0', name='ck_product_cost_price_positive'),
        CheckConstraint('sale_price >= 0', name='ck_product_sale_price_positive'),
    )
    
    def get_price_for_customer_type(self, is_vip: bool = False) -> Decimal:
        """Get appropriate price based on customer type."""
        if is_vip and self.vip_price:
            return self.vip_price
        return self.sale_price


class ProductUOMConversion(BaseModel):
    """
    Product-specific UOM conversion factors.
    
    Example for Armatura 17B:
    - Base UOM: kg
    - 1 tonna = 1000 kg (conversion_factor = 1000)
    - 1 dona = 2.68 kg (conversion_factor = 2.68)
    - 1 pochka = 200 kg (conversion_factor = 200)
    
    This allows different products to have different conversions:
    - Armatura 17B: 1 dona = 2.68 kg
    - Armatura 20B: 1 dona = 4.44 kg
    """
    
    __tablename__ = 'product_uom_conversions'
    
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    uom_id = Column(Integer, ForeignKey('units_of_measure.id'), nullable=False)
    
    # How many base units = 1 of this unit
    # Example: If base is kg and this is tonna, factor = 1000 (1 tonna = 1000 kg)
    conversion_factor = Column(Numeric(20, 10), nullable=False)
    
    # Pricing override for this UOM (optional)
    sale_price = Column(Numeric(20, 4), nullable=True)  # Price per this unit
    vip_price = Column(Numeric(20, 4), nullable=True)
    
    # Display settings
    is_default_sale_uom = Column(Boolean, default=False)  # Default UOM in sales
    is_default_purchase_uom = Column(Boolean, default=False)  # Default UOM in purchases
    is_integer_only = Column(Boolean, default=False)  # Must sell in whole numbers
    
    # Relationships
    product = relationship("Product", back_populates="uom_conversions")
    uom = relationship("UnitOfMeasure")
    
    __table_args__ = (
        UniqueConstraint('product_id', 'uom_id', name='uq_product_uom'),
        Index('ix_product_uom_product_id', 'product_id'),
        Index('ix_product_uom_uom_id', 'uom_id'),
        CheckConstraint('conversion_factor > 0', name='ck_product_uom_positive_factor'),
    )
    
    def to_base_quantity(self, quantity: Decimal) -> Decimal:
        """Convert quantity in this UOM to base UOM quantity."""
        return Decimal(str(quantity)) * Decimal(str(self.conversion_factor))
    
    def from_base_quantity(self, base_quantity: Decimal) -> Decimal:
        """Convert base UOM quantity to this UOM quantity."""
        if self.conversion_factor == 0:
            return Decimal(0)
        return Decimal(str(base_quantity)) / Decimal(str(self.conversion_factor))


class ProductPriceHistory(BaseModel):
    """
    Track product price changes for auditing.
    """
    
    __tablename__ = 'product_price_history'
    
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    changed_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    price_type = Column(String(20), nullable=False)  # cost, sale, vip
    old_price = Column(Numeric(20, 4), nullable=True)
    new_price = Column(Numeric(20, 4), nullable=False)
    reason = Column(Text, nullable=True)
    
    # Relationships
    product = relationship("Product")
    changed_by = relationship("User")
    
    __table_args__ = (
        Index('ix_price_history_product_id', 'product_id'),
        Index('ix_price_history_created_at', 'created_at'),
    )
