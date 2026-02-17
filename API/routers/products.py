"""
Products router - CRUD operations for products, categories, and UOMs.
"""

from typing import Optional, List, Union
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from database import get_db
from database.models import User, PermissionType, Product, ProductUOMConversion, UnitOfMeasure
from core.dependencies import get_current_active_user, PermissionChecker
from schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    ProductSearchParams, CategoryCreate, CategoryUpdate, CategoryResponse,
    CategoryListResponse, UOMResponse, UOMListResponse,
    ProductUOMConversionCreate, UniversalUOMConversionCreate
)
from schemas.base import SuccessResponse, DeleteResponse
from services.product import ProductService, CategoryService, UOMService


router = APIRouter()


# ==================== UNITS OF MEASURE ====================

@router.get(
    "/uom",
    response_model=UOMListResponse,
    summary="O'lchov birliklari ro'yxati"
)
async def get_uoms(
    uom_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all units of measure."""
    service = UOMService(db)
    uoms = service.get_all_uoms(uom_type)
    
    return UOMListResponse(
        data=[UOMResponse.model_validate(u) for u in uoms],
        count=len(uoms)
    )


# ==================== CATEGORIES ====================

@router.get(
    "/categories",
    response_model=CategoryListResponse,
    summary="Kategoriyalar ro'yxati"
)
async def get_categories(
    parent_id: Optional[int] = None,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get categories list."""
    service = CategoryService(db)
    categories = service.get_categories(parent_id, include_inactive)
    
    return CategoryListResponse(
        data=[CategoryResponse.model_validate(c) for c in categories],
        count=len(categories)
    )


@router.get(
    "/categories/tree",
    summary="Kategoriyalar daraxti"
)
async def get_category_tree(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get full category tree structure."""
    service = CategoryService(db)
    tree = service.get_category_tree()
    return {"success": True, "data": tree}


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Kategoriya yaratish",
    dependencies=[Depends(PermissionChecker([PermissionType.PRODUCT_CREATE]))]
)
async def create_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new category."""
    service = CategoryService(db)
    category, message = service.create_category(
        name=data.name,
        parent_id=data.parent_id,
        description=data.description,
        created_by_id=current_user.id
    )
    
    if not category:
        raise HTTPException(status_code=400, detail=message)
    
    return CategoryResponse.model_validate(category)


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Kategoriyani yangilash",
    dependencies=[Depends(PermissionChecker([PermissionType.PRODUCT_EDIT]))]
)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update category."""
    service = CategoryService(db)
    category, message = service.update_category(
        category_id,
        data.model_dump(exclude_unset=True),
        current_user.id
    )
    
    if not category:
        raise HTTPException(status_code=400, detail=message)
    
    return CategoryResponse.model_validate(category)


@router.delete(
    "/categories/{category_id}",
    response_model=DeleteResponse,
    summary="Kategoriyani o'chirish",
    dependencies=[Depends(PermissionChecker([PermissionType.PRODUCT_DELETE]))]
)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete category."""
    service = CategoryService(db)
    success, message = service.delete_category(category_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return DeleteResponse(id=category_id, message=message)


# ==================== PRODUCTS ====================

@router.get(
    "",
    response_model=ProductListResponse,
    summary="Tovarlar ro'yxati"
)
async def get_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=10000),
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    in_stock: Optional[bool] = None,
    is_active: bool = True,
    sort_by: str = "name",
    sort_order: str = "asc",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated products list with filters."""
    service = ProductService(db)

    params = ProductSearchParams(
        q=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )

    products, total = service.get_products(page, per_page, params)

    # Build response with stock info and UOM conversions
    data = []
    for p in products:
        # Get current stock in base UOM
        try:
            current_stock = sum(s.quantity for s in p.stock_items) if p.stock_items else Decimal("0")
            # Get USD cost from stock
            cost_price_usd = None
            if p.stock_items:
                for s in p.stock_items:
                    if s.last_purchase_cost_usd:
                        cost_price_usd = float(s.last_purchase_cost_usd)
                        break
        except Exception:
            current_stock = Decimal("0")
            cost_price_usd = None

        # Get UOM conversions with stock quantities
        uom_conversions = []
        for conv in p.uom_conversions:
            # Calculate stock in this UOM (base_qty / conversion_factor = qty in this UOM)
            stock_in_uom = float(current_stock) / float(conv.conversion_factor) if conv.conversion_factor else 0
            uom_conversions.append({
                "id": conv.id,
                "uom_id": conv.uom_id,
                "uom_name": conv.uom.name if conv.uom else "",
                "uom_symbol": conv.uom.symbol if conv.uom else "",
                "conversion_factor": float(conv.conversion_factor),
                "sale_price": float(conv.sale_price) if conv.sale_price else None,
                "vip_price": float(conv.vip_price) if conv.vip_price else None,
                "is_default_sale_uom": conv.is_default_sale_uom,
                "stock_quantity": round(stock_in_uom, 2),
            })

        item = {
            "id": p.id,
            "name": p.name,
            "article": p.article,
            "barcode": p.barcode,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "base_uom_id": p.base_uom_id,
            "base_uom_symbol": p.base_uom.symbol if p.base_uom else "?",
            "base_uom_name": p.base_uom.name if p.base_uom else "?",
            "cost_price": p.cost_price,
            "cost_price_usd": cost_price_usd,
            "sale_price": p.sale_price,
            "sale_price_usd": float(p.sale_price_usd) if p.sale_price_usd else None,
            "vip_price": p.vip_price,
            "vip_price_usd": float(p.vip_price_usd) if p.vip_price_usd else None,
            "min_stock_level": float(p.min_stock_level) if p.min_stock_level else 0,
            "color": p.color,
            "is_favorite": p.is_favorite or False,
            "sort_order": p.sort_order or 0,
            "image_url": p.image_url,
            "is_active": p.is_active,
            "current_stock": current_stock,
            "uom_conversions": uom_conversions
        }
        data.append(item)

    return ProductListResponse(
        data=data,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Tovar ma'lumotlari"
)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get product by ID with full details."""
    service = ProductService(db)
    product = service.get_product_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Tovar topilmadi")

    return ProductResponse.model_validate(product)


@router.get(
    "/barcode/{barcode}",
    summary="Tovarni shtrix-kod bo'yicha qidirish"
)
async def get_product_by_barcode(
    barcode: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get product by barcode (for POS scanning)."""
    service = ProductService(db)
    product = service.get_product_by_barcode(barcode)

    if not product:
        raise HTTPException(status_code=404, detail="Tovar topilmadi")

    # Calculate current stock from stock_items
    try:
        current_stock = sum(s.quantity for s in product.stock_items) if product.stock_items else Decimal("0")
        cost_price_usd = None
        if product.stock_items:
            for s in product.stock_items:
                if s.last_purchase_cost_usd:
                    cost_price_usd = float(s.last_purchase_cost_usd)
                    break
    except Exception:
        current_stock = Decimal("0")
        cost_price_usd = None

    # Build UOM conversions
    uom_conversions = []
    for conv in product.uom_conversions:
        stock_in_uom = float(current_stock) / float(conv.conversion_factor) if conv.conversion_factor else 0
        uom_conversions.append({
            "id": conv.id,
            "uom_id": conv.uom_id,
            "uom_name": conv.uom.name if conv.uom else "",
            "uom_symbol": conv.uom.symbol if conv.uom else "",
            "conversion_factor": float(conv.conversion_factor),
            "sale_price": float(conv.sale_price) if conv.sale_price else None,
            "vip_price": float(conv.vip_price) if conv.vip_price else None,
            "is_default_sale_uom": conv.is_default_sale_uom,
            "stock_quantity": round(stock_in_uom, 2),
        })

    return {
        "id": product.id,
        "name": product.name,
        "article": product.article,
        "barcode": product.barcode,
        "category_id": product.category_id,
        "category_name": product.category.name if product.category else None,
        "base_uom_id": product.base_uom_id,
        "base_uom_symbol": product.base_uom.symbol if product.base_uom else "?",
        "base_uom_name": product.base_uom.name if product.base_uom else "?",
        "cost_price": product.cost_price,
        "cost_price_usd": cost_price_usd,
        "sale_price": product.sale_price,
        "sale_price_usd": float(product.sale_price_usd) if product.sale_price_usd else None,
        "vip_price": product.vip_price,
        "vip_price_usd": float(product.vip_price_usd) if product.vip_price_usd else None,
        "min_stock_level": float(product.min_stock_level) if product.min_stock_level else 0,
        "color": product.color,
        "is_favorite": product.is_favorite or False,
        "sort_order": product.sort_order or 0,
        "image_url": product.image_url,
        "is_active": product.is_active,
        "current_stock": float(current_stock),
        "uom_conversions": uom_conversions
    }


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tovar yaratish",
    dependencies=[Depends(PermissionChecker([PermissionType.PRODUCT_CREATE]))]
)
async def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new product."""
    service = ProductService(db)
    product, message = service.create_product(data, current_user.id)

    if not product:
        raise HTTPException(status_code=400, detail=message)

    return ProductResponse.model_validate(product)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Tovarni yangilash",
    dependencies=[Depends(PermissionChecker([PermissionType.PRODUCT_EDIT]))]
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update product."""
    service = ProductService(db)
    product, message = service.update_product(product_id, data, current_user.id)

    if not product:
        raise HTTPException(status_code=400, detail=message)

    return ProductResponse.model_validate(product)


@router.delete(
    "/{product_id}",
    response_model=DeleteResponse,
    summary="Tovarni o'chirish",
    dependencies=[Depends(PermissionChecker([PermissionType.PRODUCT_DELETE]))]
)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete product (soft delete)."""
    service = ProductService(db)
    success, message = service.delete_product(product_id, current_user.id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return DeleteResponse(id=product_id, message=message)


@router.get(
    "/{product_id}/stock",
    summary="Tovar qoldiqlari"
)
async def get_product_stock(
    product_id: int,
    warehouse_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get product stock across warehouses."""
    service = ProductService(db)
    stocks = service.get_product_stock(product_id, warehouse_id)

    data = [{
        "warehouse_id": s.warehouse_id,
        "warehouse_name": s.warehouse.name,
        "quantity": s.quantity,
        "reserved": s.reserved_quantity,
        "available": s.quantity - s.reserved_quantity,
        "average_cost": s.average_cost,
        "total_value": s.quantity * s.average_cost
    } for s in stocks]

    return {"success": True, "data": data}


# ==================== UOM CONVERSIONS ====================

@router.get(
    "/{product_id}/uom-conversions",
    summary="Tovar o'lchov birlik konversiyalari"
)
async def get_product_uom_conversions(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all UOM conversions for a product."""
    product = db.query(Product).options(
        joinedload(Product.base_uom)
    ).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Tovar topilmadi")

    conversions = db.query(ProductUOMConversion).options(
        joinedload(ProductUOMConversion.uom)
    ).filter(
        ProductUOMConversion.product_id == product_id
    ).all()

    data = []
    # Add base UOM first
    data.append({
        "uom_id": product.base_uom_id,
        "uom_name": product.base_uom.name if product.base_uom else "",
        "uom_symbol": product.base_uom.symbol if product.base_uom else "",
        "conversion_factor": 1.0,
        "is_base": True,
        "sale_price": float(product.sale_price) if product.sale_price else 0,
        "vip_price": float(product.vip_price) if product.vip_price else None,
    })

    # Add other conversions
    for conv in conversions:
        data.append({
            "id": conv.id,
            "uom_id": conv.uom_id,
            "uom_name": conv.uom.name if conv.uom else "",
            "uom_symbol": conv.uom.symbol if conv.uom else "",
            "conversion_factor": float(conv.conversion_factor),
            "is_base": False,
            "sale_price": float(conv.sale_price) if conv.sale_price else None,
            "vip_price": float(conv.vip_price) if conv.vip_price else None,
            "is_default_sale_uom": conv.is_default_sale_uom,
        })

    return {"success": True, "data": data}


@router.post(
    "/{product_id}/uom-conversions",
    summary="O'lchov birlik konversiyasi qo'shish",
    dependencies=[Depends(PermissionChecker([PermissionType.PRODUCT_EDIT]))]
)
async def add_uom_conversion(
    product_id: int,
    data: UniversalUOMConversionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add UOM conversion to product using universal format.

    Example: 1 tonna = 52 dona
    - from_uom_id: tonna's ID (existing UOM)
    - to_uom_id: dona's ID (new UOM to add)
    - factor: 52

    The system calculates conversion to base UOM automatically.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Tovar topilmadi")

    # Check source UOM exists in product
    from_uom = None
    if data.from_uom_id == product.base_uom_id:
        # Source is base UOM
        from_conversion_factor = Decimal("1")
        from_uom = db.query(UnitOfMeasure).filter(UnitOfMeasure.id == data.from_uom_id).first()
    else:
        # Source is existing conversion
        from_conv = db.query(ProductUOMConversion).filter(
            ProductUOMConversion.product_id == product_id,
            ProductUOMConversion.uom_id == data.from_uom_id
        ).first()
        if not from_conv:
            raise HTTPException(status_code=400, detail="Manba o'lchov birligi tovarning o'lchov birliklarida topilmadi")
        from_conversion_factor = from_conv.conversion_factor
        from_uom = from_conv.uom

    # Check target UOM exists
    to_uom = db.query(UnitOfMeasure).filter(UnitOfMeasure.id == data.to_uom_id).first()
    if not to_uom:
        raise HTTPException(status_code=400, detail="Maqsad o'lchov birligi topilmadi")

    # Check target UOM not already in product
    existing = db.query(ProductUOMConversion).filter(
        ProductUOMConversion.product_id == product_id,
        ProductUOMConversion.uom_id == data.to_uom_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{to_uom.name}' allaqachon qo'shilgan")

    # Check not trying to add base UOM
    if data.to_uom_id == product.base_uom_id:
        raise HTTPException(status_code=400, detail="Asosiy o'lchov birligini qo'shib bo'lmaydi")

    # Calculate conversion factor to base UOM
    # Formula: new_cf = from_cf / factor
    # Example: 1 tonna (cf=1) = 52 dona → dona's cf = 1/52
    if data.factor <= 0:
        raise HTTPException(status_code=400, detail="Konversiya koeffitsienti 0 dan katta bo'lishi kerak")

    new_conversion_factor = from_conversion_factor / data.factor

    # Create conversion
    conversion = ProductUOMConversion(
        product_id=product_id,
        uom_id=data.to_uom_id,
        conversion_factor=new_conversion_factor,
        sale_price=data.sale_price,
        is_default_sale_uom=False
    )
    db.add(conversion)
    db.commit()
    db.refresh(conversion)

    return {
        "success": True,
        "message": f"1 {from_uom.symbol} = {data.factor} {to_uom.symbol} qo'shildi",
        "data": {
            "id": conversion.id,
            "uom_id": conversion.uom_id,
            "uom_name": to_uom.name,
            "uom_symbol": to_uom.symbol,
            "conversion_factor": float(conversion.conversion_factor),
            "to_base_factor": float(new_conversion_factor)
        }
    }


@router.delete(
    "/{product_id}/uom-conversions/{conversion_id}",
    summary="O'lchov birlik konversiyasini o'chirish",
    dependencies=[Depends(PermissionChecker([PermissionType.PRODUCT_EDIT]))]
)
async def delete_uom_conversion(
    product_id: int,
    conversion_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete UOM conversion from product."""
    conversion = db.query(ProductUOMConversion).filter(
        ProductUOMConversion.id == conversion_id,
        ProductUOMConversion.product_id == product_id
    ).first()

    if not conversion:
        raise HTTPException(status_code=404, detail="Konversiya topilmadi")

    db.delete(conversion)
    db.commit()

    return {"success": True, "message": "O'lchov birligi o'chirildi"}