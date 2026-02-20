"""
Warehouse router - Stock management, movements, and transfers.
"""

from typing import Optional
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from database.models import User, PermissionType, MovementType
from core.dependencies import get_current_active_user, PermissionChecker
from schemas.warehouse import (
    WarehouseCreate, WarehouseUpdate, WarehouseResponse, WarehouseListResponse,
    StockResponse, StockListResponse, StockMovementCreate, StockMovementResponse,
    StockIncomeCreate, StockTransferCreate, StockTransferResponse
)
from schemas.base import SuccessResponse, DeleteResponse
from services.warehouse import WarehouseService, StockService, StockTransferService
from utils.helpers import get_tashkent_now


router = APIRouter()


# ==================== WAREHOUSES ====================

@router.get(
    "",
    response_model=WarehouseListResponse,
    summary="Omborlar ro'yxati"
)
async def get_warehouses(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all warehouses."""
    service = WarehouseService(db)
    warehouses = service.get_warehouses(include_inactive)

    stock_service = StockService(db)

    data = []
    for w in warehouses:
        value = stock_service.get_stock_value(w.id)
        data.append({
            "id": w.id,
            "name": w.name,
            "code": w.code,
            "address": w.address,
            "phone": w.phone,
            "is_main": w.is_main,
            "is_active": w.is_active,
            "manager_id": w.manager_id,
            "total_value": value,
            "created_at": w.created_at,
            "updated_at": w.updated_at
        })

    return WarehouseListResponse(data=data, count=len(data))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Ombor yaratish",
    dependencies=[Depends(PermissionChecker([PermissionType.WAREHOUSE_CREATE]))]
)
async def create_warehouse(
    data: WarehouseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new warehouse."""
    service = WarehouseService(db)
    warehouse, message = service.create_warehouse(
        name=data.name,
        code=data.code,
        address=data.address,
        created_by_id=current_user.id
    )

    if not warehouse:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "data": {"id": warehouse.id, "name": warehouse.name}, "message": message}


# ==================== STOCK ====================

@router.get(
    "/stock",
    summary="Qoldiqlar ro'yxati"
)
async def get_stock(
    warehouse_id: Optional[int] = None,
    category_id: Optional[int] = None,
    below_minimum: Optional[bool] = None,
    out_of_stock: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get stock list with filters."""
    service = StockService(db)
    stocks, total = service.get_all_stock(
        warehouse_id=warehouse_id,
        category_id=category_id,
        below_minimum=below_minimum,
        out_of_stock=out_of_stock,
        search=search,
        page=page,
        per_page=per_page
    )

    total_value = service.get_stock_value(warehouse_id)

    data = [{
        "id": s.id,
        "product_id": s.product_id,
        "product_name": s.product.name,
        "product_article": s.product.article,
        "warehouse_id": s.warehouse_id,
        "warehouse_name": s.warehouse.name,
        "quantity": s.quantity,
        "base_uom_symbol": s.product.base_uom.symbol,
        "reserved_quantity": s.reserved_quantity,
        "available_quantity": s.quantity - s.reserved_quantity,
        "average_cost": s.average_cost,
        "total_value": s.quantity * s.average_cost,
        "min_stock_level": s.product.min_stock_level,
        "is_below_minimum": s.quantity < s.product.min_stock_level
    } for s in stocks]

    return {
        "success": True,
        "data": data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_value": total_value
    }


@router.get(
    "/stock/low",
    summary="Kam qoldiqli tovarlar"
)
async def get_low_stock(
    warehouse_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get products below minimum stock level."""
    service = StockService(db)
    low_stock = service.get_low_stock_products(warehouse_id)

    return {
        "success": True,
        "data": low_stock,
        "count": len(low_stock)
    }


@router.get(
    "/stock/value",
    summary="Ombor qiymati"
)
async def get_stock_value(
    warehouse_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get total stock value."""
    service = StockService(db)
    value = service.get_stock_value(warehouse_id)

    return {
        "success": True,
        "total_value": value,
        "warehouse_id": warehouse_id
    }


# ==================== STOCK MOVEMENTS ====================

@router.get(
    "/movements",
    summary="Harakat tarixi"
)
async def get_movements(
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get stock movements history."""
    service = StockService(db)
    movements, total = service.get_movements(
        product_id=product_id,
        warehouse_id=warehouse_id,
        movement_type=movement_type,
        start_date=start_date,
        end_date=end_date,
        search=q,
        page=page,
        per_page=per_page
    )

    data = [{
        "id": m.id,
        "product_id": m.product_id,
        "product_name": m.product.name,
        "product_article": m.product.article,
        "warehouse_id": m.warehouse_id,
        "warehouse_name": m.warehouse.name,
        "movement_type": m.movement_type.value,
        "quantity": m.quantity,
        "uom_symbol": m.uom.symbol,
        "base_quantity": m.base_quantity,
        "unit_price": m.unit_cost,  # UZS price
        "unit_price_usd": getattr(m, 'unit_price_usd', None),  # USD price
        "exchange_rate": getattr(m, 'exchange_rate', None),  # Exchange rate at time
        "total_price": m.total_cost,
        "stock_before": m.stock_before,
        "stock_after": m.stock_after,
        "reference_type": m.reference_type,
        "reference_id": m.reference_id,
        "document_number": m.document_number,
        "supplier_name": getattr(m, 'supplier_name', None),
        "notes": m.notes,
        "created_at": m.created_at.isoformat(),
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        "created_by_name": m.created_by.first_name + " " + m.created_by.last_name if m.created_by else None,
        "updated_by_name": m.updated_by.first_name + " " + m.updated_by.last_name if getattr(m, 'updated_by', None) else None
    } for m in movements]

    return {
        "success": True,
        "data": data,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.post(
    "/income",
    summary="Tovar kirim qilish",
    dependencies=[Depends(PermissionChecker([PermissionType.STOCK_INCOME]))]
)
async def stock_income(
    data: StockIncomeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Record stock income (purchase/arrival)."""
    service = StockService(db)

    results = []
    for item in data.items:
        stock, movement = service.add_stock(
            product_id=item.product_id,
            warehouse_id=data.warehouse_id,
            quantity=item.quantity,
            uom_id=item.uom_id,
            unit_cost=item.unit_price,
            movement_type=MovementType.PURCHASE,
            reference_type="manual_income",
            document_number=data.document_number,
            notes=data.notes,
            created_by_id=current_user.id,
            unit_price_usd=item.unit_price_usd,
            exchange_rate=item.exchange_rate or data.exchange_rate,
            supplier_name=data.supplier_name
        )
        results.append({
            "product_id": item.product_id,
            "new_quantity": stock.quantity,
            "movement_id": movement.id
        })

    return {
        "success": True,
        "message": f"{len(results)} ta tovar kirim qilindi",
        "data": results
    }


@router.post(
    "/adjustment",
    summary="Qoldiq tuzatish",
    dependencies=[Depends(PermissionChecker([PermissionType.STOCK_ADJUSTMENT]))]
)
async def stock_adjustment(
    data: StockMovementCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create stock adjustment (manual correction)."""
    service = StockService(db)

    movement_type = MovementType(data.movement_type)

    if movement_type in [MovementType.ADJUSTMENT_PLUS]:
        # Adding stock
        stock, movement = service.add_stock(
            product_id=data.product_id,
            warehouse_id=data.warehouse_id,
            quantity=data.quantity,
            uom_id=data.uom_id,
            unit_cost=data.unit_cost or Decimal("0"),
            movement_type=movement_type,
            document_number=data.document_number,
            notes=data.notes,
            created_by_id=current_user.id
        )
    else:
        # Removing stock
        stock, movement, msg = service.remove_stock(
            product_id=data.product_id,
            warehouse_id=data.warehouse_id,
            quantity=data.quantity,
            uom_id=data.uom_id,
            movement_type=movement_type,
            document_number=data.document_number,
            notes=data.notes,
            created_by_id=current_user.id
        )
        if not stock:
            raise HTTPException(status_code=400, detail=msg)

    return {
        "success": True,
        "message": "Qoldiq tuzatildi",
        "data": {
            "product_id": data.product_id,
            "new_quantity": stock.quantity,
            "movement_id": movement.id
        }
    }


# ==================== TRANSFERS ====================

@router.post(
    "/transfer",
    summary="Omborlar o'rtasida transfer",
    dependencies=[Depends(PermissionChecker([PermissionType.STOCK_TRANSFER]))]
)
async def create_transfer(
    data: StockTransferCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create stock transfer between warehouses."""
    service = StockTransferService(db)

    items = [item.model_dump() for item in data.items]

    transfer, message = service.create_transfer(
        from_warehouse_id=data.from_warehouse_id,
        to_warehouse_id=data.to_warehouse_id,
        items=items,
        notes=data.notes,
        created_by_id=current_user.id
    )

    if not transfer:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "data": {
            "id": transfer.id,
            "transfer_number": transfer.transfer_number,
            "status": transfer.status
        }
    }


@router.post(
    "/transfer/{transfer_id}/complete",
    summary="Transferni yakunlash",
    dependencies=[Depends(PermissionChecker([PermissionType.STOCK_TRANSFER]))]
)
async def complete_transfer(
    transfer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Complete pending transfer."""
    service = StockTransferService(db)
    success, message = service.complete_transfer(transfer_id, current_user.id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return SuccessResponse(message=message)


@router.post(
    "/transfer/{transfer_id}/cancel",
    summary="Transferni bekor qilish",
    dependencies=[Depends(PermissionChecker([PermissionType.STOCK_TRANSFER]))]
)
async def cancel_transfer(
    transfer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel pending transfer."""
    service = StockTransferService(db)
    success, message = service.cancel_transfer(transfer_id, current_user.id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return SuccessResponse(message=message)


# ==================== STOCK MOVEMENT EDIT/DELETE (DIRECTOR ONLY) ====================

@router.get(
    "/movements/{movement_id}",
    summary="Bitta harakatni olish"
)
async def get_movement(
    movement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get single stock movement by ID."""
    from database.models import StockMovement

    movement = db.query(StockMovement).filter(
        StockMovement.id == movement_id,
        StockMovement.is_deleted == False
    ).first()

    if not movement:
        raise HTTPException(status_code=404, detail="Harakat topilmadi")

    return {
        "success": True,
        "data": {
            "id": movement.id,
            "product_id": movement.product_id,
            "product_name": movement.product.name,
            "warehouse_id": movement.warehouse_id,
            "warehouse_name": movement.warehouse.name,
            "movement_type": movement.movement_type.value,
            "quantity": float(movement.quantity),
            "uom_id": movement.uom_id,
            "uom_symbol": movement.uom.symbol,
            "unit_price": float(movement.unit_cost or 0),
            "unit_price_usd": float(movement.unit_price_usd) if movement.unit_price_usd else None,
            "exchange_rate": float(movement.exchange_rate) if movement.exchange_rate else None,
            "total_price": float(movement.total_cost or 0),
            "document_number": movement.document_number,
            "supplier_name": movement.supplier_name,
            "notes": movement.notes,
            "created_at": movement.created_at.isoformat(),
            "updated_at": movement.updated_at.isoformat() if movement.updated_at else None,
            "created_by_name": f"{movement.created_by.first_name} {movement.created_by.last_name}" if movement.created_by else None,
            "updated_by_name": f"{movement.updated_by.first_name} {movement.updated_by.last_name}" if movement.updated_by else None
        }
    }


@router.put(
    "/movements/{movement_id}",
    summary="Harakatni tahrirlash (faqat Director)",
    dependencies=[Depends(PermissionChecker([PermissionType.DIRECTOR_OVERRIDE]))]
)
async def update_movement(
    movement_id: int,
    quantity: Optional[Decimal] = None,
    uom_id: Optional[int] = None,
    unit_price: Optional[Decimal] = None,
    unit_price_usd: Optional[Decimal] = None,
    exchange_rate: Optional[Decimal] = None,
    document_number: Optional[str] = None,
    supplier_name: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Edit stock movement. Only Director can do this.
    This will also update the stock quantity accordingly.
    """
    from database.models import StockMovement, Stock, ProductUOMConversion, UnitOfMeasure
    from datetime import datetime

    movement = db.query(StockMovement).filter(
        StockMovement.id == movement_id,
        StockMovement.is_deleted == False
    ).first()

    if not movement:
        raise HTTPException(status_code=404, detail="Harakat topilmadi")

    # Only allow editing PURCHASE type movements
    if movement.movement_type.value not in ['purchase', 'adjustment_plus', 'adjustment_minus']:
        raise HTTPException(status_code=400, detail="Faqat kirim va tuzatish harakatlarini tahrirlash mumkin")

    # Get current stock
    stock = db.query(Stock).filter(
        Stock.product_id == movement.product_id,
        Stock.warehouse_id == movement.warehouse_id
    ).first()

    old_quantity = movement.base_quantity

    # Handle UOM change
    target_uom_id = uom_id if uom_id is not None else movement.uom_id
    target_quantity = quantity if quantity is not None else movement.quantity

    # Calculate new base quantity
    product_uom = db.query(ProductUOMConversion).filter(
        ProductUOMConversion.product_id == movement.product_id,
        ProductUOMConversion.uom_id == target_uom_id
    ).first()

    if product_uom:
        new_base_quantity = target_quantity * Decimal(str(product_uom.conversion_factor))
    else:
        # If no conversion found, assume 1:1 (same as base UOM)
        new_base_quantity = target_quantity

    # Update stock if quantity changed
    if stock and (quantity is not None or uom_id is not None):
        quantity_diff = new_base_quantity - old_quantity
        stock.quantity = Decimal(str(stock.quantity)) + quantity_diff
        movement.stock_after = stock.quantity

    # Update movement fields
    if quantity is not None or uom_id is not None:
        movement.quantity = target_quantity
        movement.base_quantity = new_base_quantity

    if uom_id is not None:
        movement.uom_id = uom_id
        # Get UOM symbol for response
        uom = db.query(UnitOfMeasure).filter(UnitOfMeasure.id == uom_id).first()
        if uom:
            movement.uom_symbol = uom.symbol

    if unit_price is not None:
        movement.unit_cost = unit_price
        movement.total_cost = unit_price * movement.quantity

    if unit_price_usd is not None:
        movement.unit_price_usd = unit_price_usd

    if exchange_rate is not None:
        movement.exchange_rate = exchange_rate

    if document_number is not None:
        movement.document_number = document_number

    if supplier_name is not None:
        movement.supplier_name = supplier_name

    if notes is not None:
        movement.notes = notes

    # ===== RECALCULATE AVERAGE COST IN STOCK =====
    # If price changed, we need to recalculate average cost
    if unit_price_usd is not None or unit_price is not None:
        # Get all purchase movements for this product in this warehouse
        all_purchases = db.query(StockMovement).filter(
            StockMovement.product_id == movement.product_id,
            StockMovement.warehouse_id == movement.warehouse_id,
            StockMovement.movement_type.in_([MovementType.PURCHASE, MovementType.ADJUSTMENT_PLUS]),
            StockMovement.is_deleted == False
        ).all()

        # Calculate weighted average cost
        total_qty = Decimal('0')
        total_cost_uzs = Decimal('0')

        for m in all_purchases:
            qty = Decimal(str(m.base_quantity or 0))
            if qty > 0:
                total_qty += qty
                # UZS cost
                if m.unit_cost:
                    total_cost_uzs += qty * Decimal(str(m.unit_cost))

        # Update stock average cost
        if stock and total_qty > 0:
            stock.average_cost = total_cost_uzs / total_qty
            # Also update last_purchase_cost_usd if USD price was changed
            if unit_price_usd is not None:
                stock.last_purchase_cost_usd = unit_price_usd
            if unit_price is not None:
                stock.last_purchase_cost = unit_price

        # ===== UPDATE PRODUCT COST PRICE =====
        from database.models import Product
        product = db.query(Product).filter(Product.id == movement.product_id).first()
        if product:
            # Update product cost_price with new average cost or last purchase cost
            if stock and total_qty > 0:
                product.cost_price = total_cost_uzs / total_qty
            elif unit_price is not None:
                product.cost_price = unit_price

    # Track who edited
    movement.updated_by_id = current_user.id

    db.commit()

    return {
        "success": True,
        "message": "Harakat muvaffaqiyatli tahrirlandi",
        "data": {
            "id": movement.id,
            "updated_at": movement.updated_at.isoformat() if movement.updated_at else None
        }
    }


@router.delete(
    "/movements/{movement_id}",
    summary="Harakatni o'chirish (faqat Director)",
    dependencies=[Depends(PermissionChecker([PermissionType.DIRECTOR_OVERRIDE]))]
)
async def delete_movement(
    movement_id: int,
    reason: str = Query(..., min_length=3, description="O'chirish sababi"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete stock movement. Only Director can do this.
    This will also reverse the stock quantity change.
    """
    from database.models import StockMovement, Stock
    from datetime import datetime

    movement = db.query(StockMovement).filter(
        StockMovement.id == movement_id,
        StockMovement.is_deleted == False
    ).first()

    if not movement:
        raise HTTPException(status_code=404, detail="Harakat topilmadi")

    # Only allow deleting PURCHASE type movements
    if movement.movement_type.value not in ['purchase', 'adjustment_plus', 'adjustment_minus']:
        raise HTTPException(status_code=400, detail="Faqat kirim va tuzatish harakatlarini o'chirish mumkin")

    # Get current stock and reverse the change
    stock = db.query(Stock).filter(
        Stock.product_id == movement.product_id,
        Stock.warehouse_id == movement.warehouse_id
    ).first()

    if stock:
        if movement.movement_type.value in ['purchase', 'adjustment_plus']:
            # Reverse addition
            stock.quantity = Decimal(str(stock.quantity)) - movement.base_quantity
        else:
            # Reverse subtraction
            stock.quantity = Decimal(str(stock.quantity)) + movement.base_quantity

        # Ensure stock doesn't go negative
        if stock.quantity < 0:
            stock.quantity = 0

    # Soft delete
    movement.is_deleted = True
    movement.deleted_by_id = current_user.id
    movement.deleted_at = get_tashkent_now().isoformat()
    movement.deleted_reason = reason

    db.commit()

    return {
        "success": True,
        "message": "Harakat o'chirildi",
        "data": {
            "id": movement.id,
            "deleted_at": movement.deleted_at
        }
    }