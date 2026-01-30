"""
Product management service.
Handles products, categories, and UOM operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from database.models import (
    Product, Category, UnitOfMeasure, ProductUOMConversion,
    ProductPriceHistory, Stock, AuditLog, User
)
from schemas.product import ProductCreate, ProductUpdate, ProductSearchParams
from utils.helpers import generate_slug, get_tashkent_now


class ProductService:
    """Product management service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID with relationships."""
        return self.db.query(Product).filter(
            Product.id == product_id,
            Product.is_deleted == False
        ).first()
    
    def get_product_by_barcode(self, barcode: str) -> Optional[Product]:
        """Get product by barcode."""
        return self.db.query(Product).filter(
            Product.barcode == barcode,
            Product.is_deleted == False
        ).first()
    
    def get_product_by_article(self, article: str) -> Optional[Product]:
        """Get product by article."""
        return self.db.query(Product).filter(
            Product.article == article,
            Product.is_deleted == False
        ).first()
    
    def get_products(
        self,
        page: int = 1,
        per_page: int = 20,
        params: ProductSearchParams = None
    ) -> Tuple[List[Product], int]:
        """Get paginated products list with filters."""
        query = self.db.query(Product).filter(Product.is_deleted == False)
        
        if params:
            # Search by name, article, barcode
            if params.q:
                search_term = f"%{params.q}%"
                query = query.filter(
                    or_(
                        Product.name.ilike(search_term),
                        Product.article.ilike(search_term),
                        Product.barcode.ilike(search_term)
                    )
                )
            
            # Filter by category
            if params.category_id:
                query = query.filter(Product.category_id == params.category_id)
            
            # Filter by price range
            if params.min_price is not None:
                query = query.filter(Product.sale_price >= params.min_price)
            if params.max_price is not None:
                query = query.filter(Product.sale_price <= params.max_price)
            
            # Filter by active status
            if params.is_active is not None:
                query = query.filter(Product.is_active == params.is_active)
            
            # Filter by stock availability
            if params.in_stock:
                query = query.join(Stock).filter(Stock.quantity > 0)
            
            # Sorting
            sort_column = getattr(Product, params.sort_by, Product.name)
            if params.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(Product.name.asc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        products = query.offset(offset).limit(per_page).all()
        
        return products, total
    
    def create_product(
        self,
        data: ProductCreate,
        created_by_id: int
    ) -> Tuple[Optional[Product], str]:
        """Create new product."""
        
        # Check article uniqueness
        if data.article:
            existing = self.get_product_by_article(data.article)
            if existing:
                return None, "Bu artikul allaqachon mavjud"
        
        # Check barcode uniqueness
        if data.barcode:
            existing = self.get_product_by_barcode(data.barcode)
            if existing:
                return None, "Bu shtrix-kod allaqachon mavjud"
        
        # Validate base UOM exists
        base_uom = self.db.query(UnitOfMeasure).filter(
            UnitOfMeasure.id == data.base_uom_id
        ).first()
        if not base_uom:
            return None, "O'lchov birligi topilmadi"
        
        # Create product
        product = Product(
            name=data.name,
            article=data.article,
            barcode=data.barcode,
            description=data.description,
            category_id=data.category_id,
            base_uom_id=data.base_uom_id,
            cost_price=data.cost_price,
            sale_price=data.sale_price,
            vip_price=data.vip_price,
            min_stock_level=data.min_stock_level,
            track_stock=data.track_stock,
            allow_negative_stock=data.allow_negative_stock,
            image_url=data.image_url,
            brand=data.brand,
            manufacturer=data.manufacturer,
            country_of_origin=data.country_of_origin,
            is_featured=data.is_featured,
            is_service=data.is_service,
            is_active=True
        )
        
        self.db.add(product)
        self.db.flush()
        
        # Add UOM conversions
        for conv in data.uom_conversions:
            conversion = ProductUOMConversion(
                product_id=product.id,
                uom_id=conv.uom_id,
                conversion_factor=conv.conversion_factor,
                sale_price=conv.sale_price,
                vip_price=conv.vip_price,
                is_default_sale_uom=conv.is_default_sale_uom,
                is_default_purchase_uom=conv.is_default_purchase_uom,
                is_integer_only=conv.is_integer_only
            )
            self.db.add(conversion)
        
        # Log price history
        self._log_price_change(product.id, created_by_id, "sale", None, data.sale_price)
        self._log_price_change(product.id, created_by_id, "cost", None, data.cost_price)
        
        # Audit log
        self._log_action(created_by_id, "create", "products", product.id, f"Tovar yaratildi: {product.name}")
        
        self.db.commit()
        self.db.refresh(product)
        
        return product, "Tovar muvaffaqiyatli yaratildi"
    
    def update_product(
        self,
        product_id: int,
        data: ProductUpdate,
        updated_by_id: int
    ) -> Tuple[Optional[Product], str]:
        """Update product."""
        product = self.get_product_by_id(product_id)
        if not product:
            return None, "Tovar topilmadi"
        
        # Store old prices for history
        old_sale_price = product.sale_price
        old_cost_price = product.cost_price
        old_vip_price = product.vip_price
        
        # Validate base_uom_id if provided
        update_data = data.model_dump(exclude_unset=True)
        if 'base_uom_id' in update_data and update_data['base_uom_id'] is not None:
            new_uom = self.db.query(UnitOfMeasure).filter(
                UnitOfMeasure.id == update_data['base_uom_id']
            ).first()
            if not new_uom:
                return None, "O'lchov birligi topilmadi"

        # Update fields
        for field, value in update_data.items():
            if hasattr(product, field):
                setattr(product, field, value)

        # Log price changes
        if data.sale_price is not None and data.sale_price != old_sale_price:
            self._log_price_change(product.id, updated_by_id, "sale", old_sale_price, data.sale_price)

        if data.cost_price is not None and data.cost_price != old_cost_price:
            self._log_price_change(product.id, updated_by_id, "cost", old_cost_price, data.cost_price)

        if data.vip_price is not None and data.vip_price != old_vip_price:
            self._log_price_change(product.id, updated_by_id, "vip", old_vip_price, data.vip_price)

        self._log_action(updated_by_id, "update", "products", product.id, f"Tovar yangilandi: {product.name}")

        self.db.commit()
        self.db.refresh(product)

        return product, "Tovar muvaffaqiyatli yangilandi"

    def delete_product(self, product_id: int, deleted_by_id: int) -> Tuple[bool, str]:
        """Soft delete product."""
        product = self.get_product_by_id(product_id)
        if not product:
            return False, "Tovar topilmadi"

        # Check if product has stock
        stock = self.db.query(Stock).filter(
            Stock.product_id == product_id,
            Stock.quantity > 0
        ).first()

        if stock:
            return False, "Omborda qoldiq bor, avval qoldiqni 0 ga tushiring"

        product.is_deleted = True
        product.deleted_at = get_tashkent_now()
        product.is_active = False

        self._log_action(deleted_by_id, "delete", "products", product.id, f"Tovar o'chirildi: {product.name}")

        self.db.commit()
        return True, "Tovar o'chirildi"

    def add_uom_conversion(
        self,
        product_id: int,
        uom_id: int,
        conversion_factor: Decimal,
        sale_price: Optional[Decimal] = None,
        created_by_id: int = None
    ) -> Tuple[Optional[ProductUOMConversion], str]:
        """Add UOM conversion to product."""
        product = self.get_product_by_id(product_id)
        if not product:
            return None, "Tovar topilmadi"

        # Check if conversion already exists
        existing = self.db.query(ProductUOMConversion).filter(
            ProductUOMConversion.product_id == product_id,
            ProductUOMConversion.uom_id == uom_id
        ).first()

        if existing:
            return None, "Bu o'lchov birligi allaqachon qo'shilgan"

        conversion = ProductUOMConversion(
            product_id=product_id,
            uom_id=uom_id,
            conversion_factor=conversion_factor,
            sale_price=sale_price
        )

        self.db.add(conversion)
        self.db.commit()
        self.db.refresh(conversion)

        return conversion, "O'lchov birligi qo'shildi"

    def get_product_stock(self, product_id: int, warehouse_id: int = None) -> List[Stock]:
        """Get product stock in warehouses."""
        query = self.db.query(Stock).filter(Stock.product_id == product_id)

        if warehouse_id:
            query = query.filter(Stock.warehouse_id == warehouse_id)

        return query.all()

    def _log_price_change(
        self,
        product_id: int,
        changed_by_id: int,
        price_type: str,
        old_price: Optional[Decimal],
        new_price: Decimal
    ):
        """Log price change to history."""
        history = ProductPriceHistory(
            product_id=product_id,
            changed_by_id=changed_by_id,
            price_type=price_type,
            old_price=old_price,
            new_price=new_price
        )
        self.db.add(history)

    def _log_action(self, user_id: int, action: str, table: str, record_id: int, description: str):
        """Log action to audit."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table,
            record_id=record_id,
            description=description
        )
        self.db.add(log)


class CategoryService:
    """Category management service."""

    def __init__(self, db: Session):
        self.db = db

    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        return self.db.query(Category).filter(
            Category.id == category_id,
            Category.is_deleted == False
        ).first()

    def get_categories(
        self,
        parent_id: Optional[int] = None,
        include_inactive: bool = False
    ) -> List[Category]:
        """Get categories list."""
        query = self.db.query(Category).filter(Category.is_deleted == False)

        if not include_inactive:
            query = query.filter(Category.is_active == True)

        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        else:
            # Root categories only
            query = query.filter(Category.parent_id == None)

        return query.order_by(Category.sort_order, Category.name).all()

    def get_category_tree(self) -> List[dict]:
        """Get full category tree."""
        categories = self.db.query(Category).filter(
            Category.is_deleted == False,
            Category.is_active == True
        ).order_by(Category.sort_order, Category.name).all()

        # Build tree
        category_dict = {c.id: {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "parent_id": c.parent_id,
            "children": []
        } for c in categories}

        tree = []
        for cat in categories:
            if cat.parent_id is None:
                tree.append(category_dict[cat.id])
            else:
                parent = category_dict.get(cat.parent_id)
                if parent:
                    parent["children"].append(category_dict[cat.id])

        return tree

    def create_category(
        self,
        name: str,
        parent_id: Optional[int] = None,
        description: Optional[str] = None,
        created_by_id: int = None
    ) -> Tuple[Optional[Category], str]:
        """Create new category."""

        # Generate slug
        slug = generate_slug(name)

        # Check slug uniqueness
        existing = self.db.query(Category).filter(Category.slug == slug).first()
        if existing:
            slug = f"{slug}-{get_tashkent_now().strftime('%Y%m%d%H%M%S')}"

        # Validate parent exists
        if parent_id:
            parent = self.get_category_by_id(parent_id)
            if not parent:
                return None, "Ota kategoriya topilmadi"

        category = Category(
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
            is_active=True
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)

        return category, "Kategoriya yaratildi"

    def update_category(
        self,
        category_id: int,
        data: dict,
        updated_by_id: int
    ) -> Tuple[Optional[Category], str]:
        """Update category."""
        category = self.get_category_by_id(category_id)
        if not category:
            return None, "Kategoriya topilmadi"

        for field, value in data.items():
            if hasattr(category, field) and value is not None:
                setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)

        return category, "Kategoriya yangilandi"

    def delete_category(self, category_id: int, deleted_by_id: int) -> Tuple[bool, str]:
        """Soft delete category."""
        category = self.get_category_by_id(category_id)
        if not category:
            return False, "Kategoriya topilmadi"

        # Check for child categories
        children = self.db.query(Category).filter(
            Category.parent_id == category_id,
            Category.is_deleted == False
        ).count()

        if children > 0:
            return False, "Bu kategoriyada pastki kategoriyalar mavjud"

        # Check for products
        products = self.db.query(Product).filter(
            Product.category_id == category_id,
            Product.is_deleted == False
        ).count()

        if products > 0:
            return False, f"Bu kategoriyada {products} ta tovar mavjud"

        category.is_deleted = True
        category.deleted_at = get_tashkent_now()

        self.db.commit()
        return True, "Kategoriya o'chirildi"


class UOMService:
    """Unit of Measure management service."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_uoms(self, uom_type: Optional[str] = None) -> List[UnitOfMeasure]:
        """Get all units of measure."""
        query = self.db.query(UnitOfMeasure).filter(UnitOfMeasure.is_active == True)

        if uom_type:
            query = query.filter(UnitOfMeasure.uom_type == uom_type)

        return query.order_by(UnitOfMeasure.uom_type, UnitOfMeasure.name).all()

    def get_uom_by_id(self, uom_id: int) -> Optional[UnitOfMeasure]:
        """Get UOM by ID."""
        return self.db.query(UnitOfMeasure).filter(UnitOfMeasure.id == uom_id).first()

    def create_uom(
        self,
        name: str,
        symbol: str,
        uom_type: str,
        base_factor: Decimal = Decimal("1"),
        created_by_id: int = None
    ) -> Tuple[Optional[UnitOfMeasure], str]:
        """Create new unit of measure."""

        # Check uniqueness
        existing = self.db.query(UnitOfMeasure).filter(
            or_(UnitOfMeasure.name == name, UnitOfMeasure.symbol == symbol)
        ).first()

        if existing:
            return None, "Bu nom yoki belgi allaqachon mavjud"

        uom = UnitOfMeasure(
            name=name,
            symbol=symbol,
            uom_type=uom_type,
            base_factor=base_factor,
            is_active=True
        )

        self.db.add(uom)
        self.db.commit()
        self.db.refresh(uom)

        return uom, "O'lchov birligi yaratildi"