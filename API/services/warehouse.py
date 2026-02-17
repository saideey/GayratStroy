"""
Warehouse and Stock management service.
Handles inventory, stock movements, and transfers.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from database.models import (
    Warehouse, Stock, StockMovement, MovementType,
    Product, ProductUOMConversion, UnitOfMeasure,
    InventoryCheck, InventoryCheckItem, StockTransfer, StockTransferItem,
    AuditLog
)
from utils.helpers import NumberGenerator, get_tashkent_now, get_tashkent_today


class WarehouseService:
    """Warehouse management service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_warehouse_by_id(self, warehouse_id: int) -> Optional[Warehouse]:
        """Get warehouse by ID."""
        return self.db.query(Warehouse).filter(
            Warehouse.id == warehouse_id,
            Warehouse.is_deleted == False
        ).first()
    
    def get_warehouses(self, include_inactive: bool = False) -> List[Warehouse]:
        """Get all warehouses."""
        query = self.db.query(Warehouse).filter(Warehouse.is_deleted == False)
        
        if not include_inactive:
            query = query.filter(Warehouse.is_active == True)
        
        return query.order_by(Warehouse.is_main.desc(), Warehouse.name).all()
    
    def get_main_warehouse(self) -> Optional[Warehouse]:
        """Get main warehouse."""
        return self.db.query(Warehouse).filter(
            Warehouse.is_main == True,
            Warehouse.is_deleted == False
        ).first()
    
    def create_warehouse(
        self,
        name: str,
        code: str = None,
        address: str = None,
        created_by_id: int = None
    ) -> Tuple[Optional[Warehouse], str]:
        """Create new warehouse."""
        
        # Check name uniqueness
        existing = self.db.query(Warehouse).filter(
            Warehouse.name == name,
            Warehouse.is_deleted == False
        ).first()
        if existing:
            return None, "Bu nom bilan ombor mavjud"
        
        warehouse = Warehouse(
            name=name,
            code=code,
            address=address,
            is_active=True,
            is_main=False
        )
        
        self.db.add(warehouse)
        self.db.commit()
        self.db.refresh(warehouse)
        
        return warehouse, "Ombor yaratildi"
    
    def update_warehouse(
        self,
        warehouse_id: int,
        data: dict,
        updated_by_id: int
    ) -> Tuple[Optional[Warehouse], str]:
        """Update warehouse."""
        warehouse = self.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            return None, "Ombor topilmadi"
        
        for field, value in data.items():
            if hasattr(warehouse, field) and value is not None:
                setattr(warehouse, field, value)
        
        self.db.commit()
        self.db.refresh(warehouse)
        
        return warehouse, "Ombor yangilandi"


class StockService:
    """Stock management service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.num_gen = NumberGenerator(db)
    
    def get_stock(self, product_id: int, warehouse_id: int) -> Optional[Stock]:
        """Get stock for product in warehouse."""
        return self.db.query(Stock).filter(
            Stock.product_id == product_id,
            Stock.warehouse_id == warehouse_id
        ).first()
    
    def get_or_create_stock(self, product_id: int, warehouse_id: int) -> Stock:
        """Get or create stock record."""
        stock = self.get_stock(product_id, warehouse_id)
        if not stock:
            stock = Stock(
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=Decimal("0"),
                reserved_quantity=Decimal("0"),
                average_cost=Decimal("0"),
                last_purchase_cost=Decimal("0")
            )
            self.db.add(stock)
            self.db.flush()
        return stock
    
    def get_all_stock(
        self,
        warehouse_id: int = None,
        category_id: int = None,
        below_minimum: bool = None,
        out_of_stock: bool = None,
        search: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Stock], int]:
        """Get stock list with filters."""
        query = self.db.query(Stock).join(Product).filter(Product.is_deleted == False)
        
        if warehouse_id:
            query = query.filter(Stock.warehouse_id == warehouse_id)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if below_minimum:
            query = query.filter(Stock.quantity < Product.min_stock_level)
        
        if out_of_stock:
            query = query.filter(Stock.quantity <= 0)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.article.ilike(search_term)
                )
            )
        
        total = query.count()
        offset = (page - 1) * per_page
        stocks = query.offset(offset).limit(per_page).all()
        
        return stocks, total
    
    def get_available_quantity(self, product_id: int, warehouse_id: int) -> Decimal:
        """Get available quantity (total - reserved)."""
        stock = self.get_stock(product_id, warehouse_id)
        if not stock:
            return Decimal("0")
        return stock.quantity - stock.reserved_quantity
    
    def convert_to_base_uom(
        self,
        product_id: int,
        quantity: Decimal,
        uom_id: int
    ) -> Decimal:
        """Convert quantity to base UOM."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Tovar topilmadi")
        
        # If already base UOM
        if uom_id == product.base_uom_id:
            return quantity
        
        # Find conversion
        conversion = self.db.query(ProductUOMConversion).filter(
            ProductUOMConversion.product_id == product_id,
            ProductUOMConversion.uom_id == uom_id
        ).first()
        
        if not conversion:
            raise ValueError("O'lchov birligi konversiyasi topilmadi")
        
        return quantity * conversion.conversion_factor

    def add_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: Decimal,
        uom_id: int,
        unit_cost: Decimal,
        movement_type: MovementType,
        reference_type: str = None,
        reference_id: int = None,
        document_number: str = None,
        notes: str = None,
        created_by_id: int = None,
        unit_price_usd: Decimal = None,
        exchange_rate: Decimal = None,
        supplier_name: str = None
    ) -> Tuple[Stock, StockMovement]:
        """
        Add stock (income).
        Used for: purchases, returns from customer, adjustments.
        """
        # Convert to base UOM
        base_quantity = self.convert_to_base_uom(product_id, quantity, uom_id)

        stock = self.get_or_create_stock(product_id, warehouse_id)
        stock_before = stock.quantity

        # Update average cost (weighted average)
        total_value = (stock.quantity * stock.average_cost) + (base_quantity * unit_cost)
        new_quantity = stock.quantity + base_quantity

        if new_quantity > 0:
            stock.average_cost = total_value / new_quantity

        stock.quantity = new_quantity
        stock.last_purchase_cost = unit_cost
        stock.last_stock_update = get_tashkent_now().isoformat()

        # Store USD cost for dynamic exchange rate calculation
        if unit_price_usd:
            stock.last_purchase_cost_usd = unit_price_usd

        # Update product's cost_price with latest purchase cost
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product and movement_type == MovementType.PURCHASE:
            product.cost_price = unit_cost

        # Create movement record
        movement = StockMovement(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            quantity=quantity,
            uom_id=uom_id,
            base_quantity=base_quantity,
            unit_cost=unit_cost,
            total_cost=base_quantity * unit_cost,
            stock_before=stock_before,
            stock_after=stock.quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            document_number=document_number,
            notes=notes,
            created_by_id=created_by_id,
            unit_price_usd=unit_price_usd,
            exchange_rate=exchange_rate,
            supplier_name=supplier_name
        )
        self.db.add(movement)

        self.db.commit()
        return stock, movement

    def remove_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: Decimal,
        uom_id: int,
        movement_type: MovementType,
        reference_type: str = None,
        reference_id: int = None,
        document_number: str = None,
        notes: str = None,
        created_by_id: int = None
    ) -> Tuple[Optional[Stock], Optional[StockMovement], str]:
        """
        Remove stock (outcome).
        Used for: sales, returns to supplier, write-offs.
        """
        # Convert to base UOM
        base_quantity = self.convert_to_base_uom(product_id, quantity, uom_id)

        stock = self.get_stock(product_id, warehouse_id)
        if not stock:
            return None, None, "Omborda bu tovar yo'q"

        # Check availability
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product.allow_negative_stock and stock.quantity < base_quantity:
            available = stock.quantity
            return None, None, f"Yetarli qoldiq yo'q. Mavjud: {available}"

        stock_before = stock.quantity
        stock.quantity -= base_quantity
        stock.last_stock_update = get_tashkent_now().isoformat()

        # Create movement record
        movement = StockMovement(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            quantity=quantity,
            uom_id=uom_id,
            base_quantity=base_quantity,
            unit_cost=stock.average_cost,
            total_cost=base_quantity * stock.average_cost,
            stock_before=stock_before,
            stock_after=stock.quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            document_number=document_number,
            notes=notes,
            created_by_id=created_by_id
        )
        self.db.add(movement)

        self.db.commit()
        return stock, movement, "OK"

    def reserve_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: Decimal,
        uom_id: int
    ) -> Tuple[bool, str]:
        """Reserve stock for pending sale."""
        base_quantity = self.convert_to_base_uom(product_id, quantity, uom_id)

        stock = self.get_stock(product_id, warehouse_id)
        if not stock:
            return False, "Omborda bu tovar yo'q"

        available = stock.quantity - stock.reserved_quantity
        if available < base_quantity:
            return False, f"Yetarli qoldiq yo'q. Mavjud: {available}"

        stock.reserved_quantity += base_quantity
        self.db.commit()

        return True, "Rezerv qilindi"

    def release_reservation(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: Decimal,
        uom_id: int
    ):
        """Release reserved stock."""
        base_quantity = self.convert_to_base_uom(product_id, quantity, uom_id)

        stock = self.get_stock(product_id, warehouse_id)
        if stock:
            stock.reserved_quantity = max(Decimal("0"), stock.reserved_quantity - base_quantity)
            self.db.commit()

    def get_movements(
        self,
        product_id: int = None,
        warehouse_id: int = None,
        movement_type: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        search: str = None,
        page: int = 1,
        per_page: int = 20,
        include_deleted: bool = False
    ) -> Tuple[List[StockMovement], int]:
        """Get stock movements with filters."""
        query = self.db.query(StockMovement)

        # Exclude deleted by default
        if not include_deleted:
            query = query.filter(
                (StockMovement.is_deleted == False) | (StockMovement.is_deleted == None)
            )

        if product_id:
            query = query.filter(StockMovement.product_id == product_id)

        if warehouse_id:
            query = query.filter(StockMovement.warehouse_id == warehouse_id)

        # Search by product name or article
        if search:
            search_term = f"%{search}%"
            print(f"[SEARCH DEBUG] Searching for: '{search}', search_term: '{search_term}'")

            # Find matching product IDs first (simple list approach)
            matching_products = self.db.query(Product.id, Product.name).filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.article.ilike(search_term)
                )
            ).all()

            print(f"[SEARCH DEBUG] Found {len(matching_products)} matching products")
            for p in matching_products[:5]:
                print(f"[SEARCH DEBUG]   - Product ID: {p.id}, Name: {p.name}")

            # Extract IDs as list
            product_ids = [p.id for p in matching_products]
            if product_ids:
                query = query.filter(StockMovement.product_id.in_(product_ids))
                print(f"[SEARCH DEBUG] Filtering movements by {len(product_ids)} product IDs")
            else:
                # No matching products found - return empty result
                print(f"[SEARCH DEBUG] No matching products found, returning empty")
                return [], 0

        if movement_type:
            # Database enum uses uppercase values (PURCHASE, SALE, etc.)
            valid_types = {'purchase': 'PURCHASE', 'sale': 'SALE', 'transfer_in': 'TRANSFER_IN',
                          'transfer_out': 'TRANSFER_OUT', 'adjustment_plus': 'ADJUSTMENT_PLUS',
                          'adjustment_minus': 'ADJUSTMENT_MINUS', 'return_from_customer': 'RETURN_FROM_CUSTOMER',
                          'return_to_supplier': 'RETURN_TO_SUPPLIER', 'write_off': 'WRITE_OFF',
                          'internal_use': 'INTERNAL_USE'}
            movement_type_lower = movement_type.lower()
            if movement_type_lower in valid_types:
                from sqlalchemy import text
                db_value = valid_types[movement_type_lower]
                # Cast string to PostgreSQL enum type
                query = query.filter(text(f"stock_movements.movement_type = '{db_value}'::movementtype"))

        if start_date:
            query = query.filter(StockMovement.created_at >= start_date)

        if end_date:
            query = query.filter(StockMovement.created_at <= end_date)

        total = query.count()
        offset = (page - 1) * per_page
        movements = query.order_by(StockMovement.created_at.desc()).offset(offset).limit(per_page).all()

        if search:
            print(f"[SEARCH DEBUG] Final results - Total: {total}, Returned: {len(movements)}")
            for m in movements[:3]:
                print(f"[SEARCH DEBUG]   - Movement ID: {m.id}, Product: {m.product.name if m.product else 'N/A'}")

        return movements, total

    def get_stock_value(self, warehouse_id: int = None) -> Decimal:
        """Get total stock value."""
        query = self.db.query(
            func.sum(Stock.quantity * Stock.average_cost)
        )

        if warehouse_id:
            query = query.filter(Stock.warehouse_id == warehouse_id)

        result = query.scalar()
        return result or Decimal("0")

    def get_low_stock_products(self, warehouse_id: int = None) -> List[dict]:
        """Get products below minimum stock level."""
        query = self.db.query(Stock, Product).join(Product).filter(
            Product.is_deleted == False,
            Product.track_stock == True,
            Product.min_stock_level > 0,  # Only products with min_stock set
            Stock.quantity < Product.min_stock_level
        )

        if warehouse_id:
            query = query.filter(Stock.warehouse_id == warehouse_id)

        results = query.all()

        return [{
            "product_id": product.id,
            "product_name": product.name,
            "article": product.article,
            "current_stock": float(stock.quantity),
            "min_stock": float(product.min_stock_level),
            "shortage": float(product.min_stock_level - stock.quantity),
            "base_uom_symbol": product.base_uom.symbol if product.base_uom else "dona",
            "warehouse_id": stock.warehouse_id,
            "warehouse_name": stock.warehouse.name if stock.warehouse else None
        } for stock, product in results]


class StockTransferService:
    """Stock transfer between warehouses."""

    def __init__(self, db: Session):
        self.db = db
        self.stock_service = StockService(db)
        self.num_gen = NumberGenerator(db)

    def create_transfer(
        self,
        from_warehouse_id: int,
        to_warehouse_id: int,
        items: List[dict],
        notes: str = None,
        created_by_id: int = None
    ) -> Tuple[Optional[StockTransfer], str]:
        """Create stock transfer."""

        if from_warehouse_id == to_warehouse_id:
            return None, "Bir xil omborlar orasida transfer mumkin emas"

        # Validate warehouses
        from_wh = self.db.query(Warehouse).filter(Warehouse.id == from_warehouse_id).first()
        to_wh = self.db.query(Warehouse).filter(Warehouse.id == to_warehouse_id).first()

        if not from_wh or not to_wh:
            return None, "Ombor topilmadi"

        # Create transfer
        transfer = StockTransfer(
            transfer_number=self.num_gen.get_next_transfer_number(),
            transfer_date=get_tashkent_today(),
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            status="PENDING",
            notes=notes,
            created_by_id=created_by_id
        )
        self.db.add(transfer)
        self.db.flush()

        # Add items and check availability
        for item in items:
            # Check stock availability
            available = self.stock_service.get_available_quantity(
                item["product_id"], from_warehouse_id
            )
            base_qty = self.stock_service.convert_to_base_uom(
                item["product_id"], item["quantity"], item["uom_id"]
            )

            if available < base_qty:
                self.db.rollback()
                product = self.db.query(Product).filter(Product.id == item["product_id"]).first()
                return None, f"'{product.name}' uchun yetarli qoldiq yo'q"

            transfer_item = StockTransferItem(
                stock_transfer_id=transfer.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                uom_id=item["uom_id"],
                base_quantity=base_qty,
                notes=item.get("notes")
            )
            self.db.add(transfer_item)

            # Reserve stock
            self.stock_service.reserve_stock(
                item["product_id"], from_warehouse_id,
                item["quantity"], item["uom_id"]
            )

        self.db.commit()
        self.db.refresh(transfer)

        return transfer, "Transfer yaratildi"

    def complete_transfer(
        self,
        transfer_id: int,
        received_by_id: int
    ) -> Tuple[bool, str]:
        """Complete transfer - move stock from source to destination."""
        transfer = self.db.query(StockTransfer).filter(
            StockTransfer.id == transfer_id
        ).first()

        if not transfer:
            return False, "Transfer topilmadi"

        if transfer.status != "PENDING":
            return False, "Bu transfer allaqachon bajarilgan"

        # Process each item
        for item in transfer.items:
            # Release reservation and remove from source
            self.stock_service.release_reservation(
                item.product_id, transfer.from_warehouse_id,
                item.quantity, item.uom_id
            )

            stock = self.stock_service.get_stock(item.product_id, transfer.from_warehouse_id)
            unit_cost = stock.average_cost if stock else Decimal("0")

            self.stock_service.remove_stock(
                product_id=item.product_id,
                warehouse_id=transfer.from_warehouse_id,
                quantity=item.quantity,
                uom_id=item.uom_id,
                movement_type=MovementType.TRANSFER_OUT,
                reference_type="stock_transfer",
                reference_id=transfer.id,
                created_by_id=received_by_id
            )

            # Add to destination
            self.stock_service.add_stock(
                product_id=item.product_id,
                warehouse_id=transfer.to_warehouse_id,
                quantity=item.quantity,
                uom_id=item.uom_id,
                unit_cost=unit_cost,
                movement_type=MovementType.TRANSFER_IN,
                reference_type="stock_transfer",
                reference_id=transfer.id,
                created_by_id=received_by_id
            )

            item.received_quantity = item.quantity
            item.base_received_quantity = item.base_quantity

        transfer.status = "COMPLETED"
        transfer.received_by_id = received_by_id
        transfer.received_at = get_tashkent_now().isoformat()

        self.db.commit()
        return True, "Transfer bajarildi"

    def cancel_transfer(
        self,
        transfer_id: int,
        cancelled_by_id: int
    ) -> Tuple[bool, str]:
        """Cancel pending transfer."""
        transfer = self.db.query(StockTransfer).filter(
            StockTransfer.id == transfer_id
        ).first()

        if not transfer:
            return False, "Transfer topilmadi"

        if transfer.status != "PENDING":
            return False, "Faqat kutilayotgan transferni bekor qilish mumkin"

        # Release all reservations
        for item in transfer.items:
            self.stock_service.release_reservation(
                item.product_id, transfer.from_warehouse_id,
                item.quantity, item.uom_id
            )

        transfer.status = "CANCELLED"
        self.db.commit()

        return True, "Transfer bekor qilindi"