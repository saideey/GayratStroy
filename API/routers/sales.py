"""
Sales router - Sale operations with proportional discount support.
"""

from typing import Optional
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from database.models import User, PermissionType
from database.models.sale import PaymentStatus
from core.dependencies import get_current_active_user, PermissionChecker
from schemas.sale import (
    SaleCreate, SaleResponse, SaleListResponse, SaleSearchParams,
    PaymentCreate, SaleCancelRequest, QuickSaleRequest
)
from schemas.base import SuccessResponse
from services.sale import SaleService
from services.telegram_notifier import send_payment_notification_sync
from utils.print_helper import queue_receipt_for_printing


router = APIRouter()


@router.get(
    "",
    summary="Sotuvlar ro'yxati"
)
async def get_sales(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = Query(None),
    seller_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    payment_status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    is_cancelled: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated sales list with filters."""
    from database.models import Sale, RoleType
    
    service = SaleService(db)
    
    # Agar director bo'lmasa, faqat o'z sotuvlarini ko'radi
    is_director = current_user.role and current_user.role.role_type == RoleType.DIRECTOR
    effective_seller_id = seller_id
    if not is_director:
        effective_seller_id = current_user.id
    
    sales, total, summary = service.get_sales(
        page=page,
        per_page=per_page,
        customer_id=customer_id,
        seller_id=effective_seller_id,
        warehouse_id=warehouse_id,
        payment_status=payment_status,
        start_date=start_date,
        end_date=end_date,
        is_cancelled=is_cancelled
    )
    
    # Har bir sotuvchi uchun oxirgi sotuv ID sini topish
    last_sale_ids = {}
    if not is_director:
        # Faqat joriy foydalanuvchining oxirgi sotuvini tekshirish
        last_sale = db.query(Sale).filter(
            Sale.seller_id == current_user.id,
            Sale.is_cancelled == False
        ).order_by(Sale.id.desc()).first()
        if last_sale:
            last_sale_ids[current_user.id] = last_sale.id
    
    data = [{
        "id": s.id,
        "sale_number": s.sale_number,
        "sale_date": s.sale_date.isoformat(),
        "customer_id": s.customer_id,
        "customer_name": s.customer.name if s.customer else None,
        "seller_id": s.seller_id,
        "seller_name": f"{s.seller.first_name} {s.seller.last_name}",
        "total_amount": s.total_amount,
        "paid_amount": s.paid_amount,
        "debt_amount": s.debt_amount,
        "payment_status": s.payment_status.value,
        "items_count": s.items.count(),
        "is_cancelled": s.is_cancelled,
        "created_at": s.created_at.isoformat(),
        # Sotuvchi uchun: faqat oxirgi sotuvni tahrirlash mumkin
        "can_edit": is_director or (s.seller_id == current_user.id and s.id == last_sale_ids.get(current_user.id)),
        "is_own_sale": s.seller_id == current_user.id
    } for s in sales]
    
    return {
        "success": True,
        "data": data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "summary": {
            "total_amount": summary["total_amount"],
            "total_paid": summary["total_paid"],
            "total_debt": summary["total_debt"]
        },
        "is_director": is_director
    }


@router.get(
    "/daily-summary",
    summary="Kunlik hisobot"
)
async def get_daily_summary(
    sale_date: Optional[date] = None,
    warehouse_id: Optional[int] = None,
    seller_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get daily sales summary."""
    service = SaleService(db)
    
    if not sale_date:
        sale_date = date.today()
    
    summary = service.get_daily_summary(sale_date, warehouse_id, seller_id)
    
    return {"success": True, "data": summary}


@router.get(
    "/seller-summary",
    summary="Sotuvchi hisoboti"
)
async def get_seller_summary(
    seller_id: int,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get sales summary for specific seller."""
    service = SaleService(db)
    summary = service.get_seller_summary(seller_id, start_date, end_date)
    
    return {"success": True, "data": summary}


@router.get(
    "/{sale_id}",
    summary="Sotuv ma'lumotlari"
)
async def get_sale(
    sale_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get sale by ID with full details."""
    service = SaleService(db)
    sale = service.get_sale_by_id(sale_id)
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sotuv topilmadi")
    
    # Build response
    items = [{
        "id": item.id,
        "product_id": item.product_id,
        "product_name": item.product.name,
        "product_article": item.product.article,
        "quantity": item.quantity,
        "uom_id": item.uom_id,
        "uom_symbol": item.uom.symbol,
        "base_quantity": item.base_quantity,
        "original_price": item.original_price,
        "unit_price": item.unit_price,
        "discount_percent": item.discount_percent,
        "discount_amount": item.discount_amount,
        "total_price": item.total_price,
        "unit_cost": item.unit_cost,
        "notes": item.notes
    } for item in sale.items]
    
    payments = [{
        "id": p.id,
        "payment_number": p.payment_number,
        "payment_date": p.payment_date.isoformat(),
        "payment_type": p.payment_type.value,
        "amount": p.amount,
        "is_confirmed": p.is_confirmed
    } for p in sale.payments]
    
    return {
        "success": True,
        "data": {
            "id": sale.id,
            "sale_number": sale.sale_number,
            "sale_date": sale.sale_date.isoformat(),
            "customer_id": sale.customer_id,
            "customer_name": sale.customer.name if sale.customer else None,
            "customer_phone": sale.customer.phone if sale.customer else None,
            "seller_id": sale.seller_id,
            "seller_name": f"{sale.seller.first_name} {sale.seller.last_name}",
            "warehouse_id": sale.warehouse_id,
            "warehouse_name": sale.warehouse.name,
            "subtotal": sale.subtotal,
            "discount_amount": sale.discount_amount,
            "discount_percent": sale.discount_percent,
            "total_amount": sale.total_amount,
            "paid_amount": sale.paid_amount,
            "debt_amount": sale.debt_amount,
            "payment_status": sale.payment_status.value,
            "payment_type": sale.payment_type.value if sale.payment_type else None,
            "items": items,
            "payments": payments,
            "requires_delivery": sale.requires_delivery,
            "delivery_address": sale.delivery_address,
            "delivery_date": sale.delivery_date.isoformat() if sale.delivery_date else None,
            "delivery_cost": sale.delivery_cost,
            "is_vip_sale": sale.is_vip_sale,
            "is_cancelled": sale.is_cancelled,
            "cancelled_reason": sale.cancelled_reason,
            "cancelled_at": sale.cancelled_at,
            "cancelled_by": f"{sale.cancelled_by.first_name} {sale.cancelled_by.last_name}" if sale.cancelled_by else None,
            "notes": sale.notes,
            "created_at": sale.created_at.isoformat(),
            "updated_at": sale.updated_at.isoformat() if sale.updated_at else None,
            "updated_by": f"{sale.updated_by.first_name} {sale.updated_by.last_name}" if sale.updated_by else None,
            "edit_reason": sale.edit_reason
        }
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Sotuv yaratish",
    dependencies=[Depends(PermissionChecker([PermissionType.SALE_CREATE]))]
)
async def create_sale(
    data: SaleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create new sale with optional proportional discount.
    
    If `final_total` is provided and less than calculated subtotal,
    the discount will be distributed proportionally across all items.
    
    Example:
    - Items total: 3,500,000 so'm
    - final_total: 3,000,000 so'm
    - Each item gets ~14.3% discount proportionally
    """
    service = SaleService(db)
    
    # Prepare items
    items = [item.model_dump() for item in data.items]
    
    # Prepare payments
    payments = [p.model_dump() for p in data.payments] if data.payments else []
    
    sale, message = service.create_sale(
        seller_id=current_user.id,
        warehouse_id=data.warehouse_id,
        items=items,
        customer_id=data.customer_id,
        final_total=data.final_total,
        payments=payments,
        notes=data.notes,
        requires_delivery=data.requires_delivery,
        delivery_address=data.delivery_address,
        delivery_date=data.delivery_date,
        delivery_cost=data.delivery_cost
    )
    
    if not sale:
        raise HTTPException(status_code=400, detail=message)

    try:
        # Get company phones from settings
        company_phones_setting = db.query(SystemSetting).filter(
            SystemSetting.key == "company_phones"
        ).first()

        company_phones = []
        if company_phones_setting and company_phones_setting.value:
            import json
            phones_data = json.loads(company_phones_setting.value)
            if phones_data.get('phone1'):
                company_phones.append(phones_data['phone1'])
            if phones_data.get('phone2'):
                company_phones.append(phones_data['phone2'])

        # Queue receipt
        print_job_id = queue_receipt_for_printing(
            db=db,
            sale=sale,  # Sale object with items loaded
            user_id=current_user.id,
            company_name="METALL BAZA",  # Yoki settings dan oling
            company_phones=company_phones
        )

        if print_job_id:
            print(f"[PRINT] Receipt queued: job_id={print_job_id}")
    except Exception as e:
        # Print error should not fail the sale
        print(f"[PRINT ERROR] {e}")
    
    return {
        "success": True,
        "message": message,
        "data": {
            "id": sale.id,
            "sale_number": sale.sale_number,
            "total_amount": sale.total_amount,
            "paid_amount": sale.paid_amount,
            "debt_amount": sale.debt_amount,
            "discount_amount": sale.discount_amount,
            "discount_percent": sale.discount_percent,
            "payment_status": sale.payment_status.value
        }
    }


@router.post(
    "/quick",
    status_code=status.HTTP_201_CREATED,
    summary="Tezkor sotuv (POS)",
    dependencies=[Depends(PermissionChecker([PermissionType.SALE_CREATE]))]
)
async def quick_sale(
    data: QuickSaleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Quick sale for POS - simplified creation with single payment.
    """
    service = SaleService(db)
    
    items = [item.model_dump() for item in data.items]
    
    # Single payment
    payments = [{
        "payment_type": data.payment_type,
        "amount": data.payment_amount
    }]
    
    sale, message = service.create_sale(
        seller_id=current_user.id,
        warehouse_id=data.warehouse_id,
        items=items,
        customer_id=data.customer_id,
        final_total=data.final_total,
        payments=payments,
        notes=data.notes
    )
    
    if not sale:
        raise HTTPException(status_code=400, detail=message)
    
    # Calculate change
    change = max(Decimal("0"), data.payment_amount - sale.total_amount)
    
    return {
        "success": True,
        "message": message,
        "data": {
            "id": sale.id,
            "sale_number": sale.sale_number,
            "total_amount": sale.total_amount,
            "paid_amount": sale.paid_amount,
            "change": change,
            "payment_status": sale.payment_status.value
        }
    }


@router.post(
    "/{sale_id}/payment",
    summary="To'lov qo'shish",
    dependencies=[Depends(PermissionChecker([PermissionType.PAYMENT_CREATE]))]
)
async def add_payment(
    sale_id: int,
    data: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add payment to existing sale."""
    service = SaleService(db)
    
    # Get sale before payment to get previous debt
    sale_before = service.get_sale_by_id(sale_id)
    if not sale_before:
        raise HTTPException(status_code=404, detail="Sotuv topilmadi")
    
    previous_debt = float(sale_before.debt_amount) if sale_before else 0
    
    payment, message = service.add_payment(
        sale_id=sale_id,
        payment_type=data.payment_type,
        amount=data.amount,
        received_by_id=current_user.id,
        transaction_id=data.transaction_id,
        notes=data.notes
    )
    
    if not payment:
        raise HTTPException(status_code=400, detail=message)
    
    sale = service.get_sale_by_id(sale_id)
    
    # Send Telegram notification for payment
    try:
        from database.models import Customer
        customer = None
        if sale.customer_id:
            customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()
        
        operator_name = f"{current_user.first_name} {current_user.last_name}"
        
        send_payment_notification_sync(
            customer_telegram_id=customer.telegram_id if customer else None,
            customer_name=customer.name if customer else "Noma'lum mijoz",
            customer_phone=customer.phone if customer else "",
            customer_type=customer.customer_type.name if customer else "STANDARD",
            payment_date=payment.created_at,
            payment_amount=float(data.amount),
            payment_type=data.payment_type.value,
            previous_debt=previous_debt,
            current_debt=float(sale.debt_amount),
            operator_name=operator_name
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to send payment notification: {e}")
    
    return {
        "success": True,
        "message": message,
        "data": {
            "payment_id": payment.id,
            "payment_number": payment.payment_number,
            "remaining_debt": sale.debt_amount,
            "payment_status": sale.payment_status.value
        }
    }


@router.post(
    "/{sale_id}/cancel",
    summary="Sotuvni bekor qilish",
    dependencies=[Depends(PermissionChecker([PermissionType.SALE_CANCEL]))]
)
async def cancel_sale(
    sale_id: int,
    data: SaleCancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel sale and optionally return items to stock."""
    service = SaleService(db)
    
    success, message = service.cancel_sale(
        sale_id=sale_id,
        reason=data.reason,
        return_to_stock=data.return_to_stock,
        cancelled_by_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return SuccessResponse(message=message)


# ==================== SALE EDIT (DIRECTOR ONLY) ====================

@router.put(
    "/{sale_id}",
    summary="Sotuvni tahrirlash (faqat Director)",
    dependencies=[Depends(PermissionChecker([PermissionType.DIRECTOR_OVERRIDE]))]
)
async def update_sale(
    sale_id: int,
    customer_id: Optional[int] = None,
    total_amount: Optional[Decimal] = None,
    paid_amount: Optional[Decimal] = None,
    notes: Optional[str] = None,
    edit_reason: str = Query(..., min_length=3, description="Tahrirlash sababi"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Edit sale details. Only Director can do this.
    Can change: customer, total amount, paid amount, notes.
    """
    from database.models import Sale, Customer, PaymentStatus
    
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sotuv topilmadi")
    
    if sale.is_cancelled:
        raise HTTPException(status_code=400, detail="Bekor qilingan sotuvni tahrirlab bo'lmaydi")
    
    # Update customer
    if customer_id is not None:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Mijoz topilmadi")
        
        # Update old customer's debt if had debt
        if sale.customer_id and sale.debt_amount > 0:
            old_customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()
            if old_customer:
                old_customer.current_debt = Decimal(str(old_customer.current_debt or 0)) - sale.debt_amount
        
        # Update new customer's debt
        if sale.debt_amount > 0:
            customer.current_debt = Decimal(str(customer.current_debt or 0)) + sale.debt_amount
        
        sale.customer_id = customer_id
    
    # Update total amount
    if total_amount is not None:
        old_total = sale.total_amount
        sale.total_amount = total_amount
        sale.discount_amount = sale.subtotal - total_amount
        if sale.subtotal > 0:
            sale.discount_percent = (sale.discount_amount / sale.subtotal) * 100
        
        # Recalculate debt if changed
        if sale.paid_amount:
            sale.debt_amount = max(Decimal('0'), total_amount - sale.paid_amount)
            
            # Update customer debt
            if sale.customer_id:
                customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()
                if customer:
                    debt_diff = sale.debt_amount - (old_total - sale.paid_amount)
                    customer.current_debt = Decimal(str(customer.current_debt or 0)) + debt_diff
    
    # Update paid amount
    if paid_amount is not None:
        old_paid = sale.paid_amount
        sale.paid_amount = paid_amount
        sale.debt_amount = max(Decimal('0'), sale.total_amount - paid_amount)
        
        # Update payment status
        if sale.debt_amount == 0:
            sale.payment_status = PaymentStatus.PAID
        elif paid_amount > 0:
            sale.payment_status = PaymentStatus.PARTIAL
        else:
            sale.payment_status = PaymentStatus.DEBT
        
        # Update customer debt
        if sale.customer_id:
            customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()
            if customer:
                debt_diff = sale.debt_amount - (sale.total_amount - old_paid)
                customer.current_debt = Decimal(str(customer.current_debt or 0)) + debt_diff
    
    # Update notes
    if notes is not None:
        sale.notes = notes
    
    # Track edit
    sale.updated_by_id = current_user.id
    sale.edit_reason = edit_reason
    
    db.commit()
    
    return {
        "success": True,
        "message": "Sotuv muvaffaqiyatli tahrirlandi",
        "data": {
            "id": sale.id,
            "sale_number": sale.sale_number,
            "total_amount": float(sale.total_amount),
            "paid_amount": float(sale.paid_amount),
            "debt_amount": float(sale.debt_amount),
            "updated_at": sale.updated_at.isoformat() if sale.updated_at else None,
            "updated_by": f"{current_user.first_name} {current_user.last_name}"
        }
    }


def can_user_edit_sale(user: User, sale_id: int, db: Session) -> tuple[bool, str]:
    """
    Check if user can edit/delete a sale.
    - Director: can edit any sale
    - Seller: can only edit their own LAST sale
    
    Returns: (can_edit, error_message)
    """
    from database.models import Sale, RoleType
    
    # Director can edit anything
    if user.role and user.role.role_type == RoleType.DIRECTOR:
        return True, ""
    
    # Get the sale
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        return False, "Sotuv topilmadi"
    
    # Check if it's user's own sale
    if sale.seller_id != user.id:
        return False, "Siz faqat o'z sotuvlaringizni tahrirlashingiz mumkin"
    
    # Check if it's their last sale
    last_sale = db.query(Sale).filter(
        Sale.seller_id == user.id,
        Sale.is_cancelled == False
    ).order_by(Sale.id.desc()).first()
    
    if not last_sale or last_sale.id != sale_id:
        return False, "Siz faqat oxirgi sotuvingizni tahrirlashingiz mumkin. Yangi sotuv qilganingizdan keyin avvalgi sotuvlarni o'zgartira olmaysiz."
    
    return True, ""


@router.delete(
    "/{sale_id}",
    summary="Sotuvni o'chirish"
)
async def delete_sale(
    sale_id: int,
    reason: str = Query(..., min_length=3, description="O'chirish sababi"),
    return_to_stock: bool = Query(True, description="Tovarlarni omborga qaytarish"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete (cancel) sale.
    - Director: can delete any sale
    - Seller: can only delete their own LAST sale
    """
    # Check permission
    can_edit, error_msg = can_user_edit_sale(current_user, sale_id, db)
    if not can_edit:
        raise HTTPException(status_code=403, detail=error_msg)
    
    from database.models import RoleType
    service = SaleService(db)
    
    is_director = current_user.role and current_user.role.role_type == RoleType.DIRECTOR
    reason_prefix = "[DIRECTOR O'CHIRDI]" if is_director else "[SOTUVCHI O'CHIRDI]"
    
    success, message = service.cancel_sale(
        sale_id=sale_id,
        reason=f"{reason_prefix} {reason}",
        return_to_stock=return_to_stock,
        cancelled_by_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": "Sotuv o'chirildi (bekor qilindi)"
    }


@router.put(
    "/{sale_id}/full",
    summary="Sotuvni to'liq tahrirlash"
)
async def full_update_sale(
    sale_id: int,
    data: SaleCreate,
    edit_reason: str = Query(..., min_length=3, description="Tahrirlash sababi"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Full update sale - replace all items and recalculate.
    - Director: can edit any sale
    - Seller: can only edit their own LAST sale
    
    This will:
    1. Return old items to stock
    2. Deduct new items from stock
    3. Update all sale data
    """
    # Check permission
    can_edit, error_msg = can_user_edit_sale(current_user, sale_id, db)
    if not can_edit:
        raise HTTPException(status_code=403, detail=error_msg)
    
    from database.models import Sale, SaleItem, Customer, Stock, StockMovement, Product, ProductUOMConversion
    from database.models.warehouse import MovementType
    from datetime import datetime
    
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sotuv topilmadi")
    
    if sale.is_cancelled:
        raise HTTPException(status_code=400, detail="Bekor qilingan sotuvni tahrirlab bo'lmaydi")
    
    # 1. Return old items to stock
    for old_item in sale.items:
        stock = db.query(Stock).filter(
            Stock.product_id == old_item.product_id,
            Stock.warehouse_id == sale.warehouse_id
        ).first()
        
        if stock:
            stock.quantity = Decimal(str(stock.quantity)) + old_item.base_quantity
    
    # 2. Update customer debt (remove old debt)
    old_customer = sale.customer
    if old_customer and sale.debt_amount > 0:
        old_customer.current_debt = Decimal(str(old_customer.current_debt or 0)) - sale.debt_amount
    
    # 3. Delete old items
    db.query(SaleItem).filter(SaleItem.sale_id == sale_id).delete()
    
    # 4. Create new items and deduct from stock
    subtotal = Decimal('0')
    new_items = []
    
    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Tovar topilmadi: {item_data.product_id}")
        
        # Get UOM conversion
        product_uom = db.query(ProductUOMConversion).filter(
            ProductUOMConversion.product_id == item_data.product_id,
            ProductUOMConversion.uom_id == item_data.uom_id
        ).first()
        
        conversion_factor = Decimal(str(product_uom.conversion_factor)) if product_uom else Decimal('1')
        base_quantity = Decimal(str(item_data.quantity)) * conversion_factor
        
        unit_price = Decimal(str(item_data.unit_price)) if item_data.unit_price else Decimal(str(product.sale_price or 0))
        original_price = Decimal(str(getattr(item_data, 'original_price', None) or item_data.unit_price or product.sale_price or 0))
        total_price = unit_price * Decimal(str(item_data.quantity))
        
        # Deduct from stock
        stock = db.query(Stock).filter(
            Stock.product_id == item_data.product_id,
            Stock.warehouse_id == sale.warehouse_id
        ).first()
        
        if stock:
            stock.quantity = Decimal(str(stock.quantity)) - base_quantity
        
        # Create sale item
        sale_item = SaleItem(
            sale_id=sale_id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            uom_id=item_data.uom_id,
            base_quantity=base_quantity,
            unit_price=unit_price,
            original_price=original_price,
            total_price=total_price,
            discount_percent=getattr(item_data, 'discount_percent', 0) or 0,
            discount_amount=getattr(item_data, 'discount_amount', 0) or 0,
            notes=item_data.notes
        )
        new_items.append(sale_item)
        subtotal += total_price
    
    db.add_all(new_items)
    
    # 5. Update sale header
    final_total = Decimal(str(data.final_total)) if data.final_total else subtotal
    discount_amount = subtotal - final_total if final_total < subtotal else Decimal('0')
    discount_percent = (discount_amount / subtotal * 100) if subtotal > 0 else Decimal('0')
    
    sale.customer_id = data.customer_id
    sale.warehouse_id = data.warehouse_id
    sale.subtotal = subtotal
    sale.discount_amount = discount_amount
    sale.discount_percent = discount_percent
    sale.total_amount = final_total
    sale.notes = data.notes
    
    # 6. Update payment info
    paid_amount = Decimal('0')
    if data.payments:
        for payment_data in data.payments:
            paid_amount += Decimal(str(payment_data.amount))
    
    debt_amount = max(Decimal('0'), final_total - paid_amount)
    
    sale.paid_amount = paid_amount
    sale.debt_amount = debt_amount
    
    # Update payment status
    if debt_amount == 0:
        sale.payment_status = PaymentStatus.PAID
    elif paid_amount > 0:
        sale.payment_status = PaymentStatus.PARTIAL
    else:
        sale.payment_status = PaymentStatus.DEBT
    
    # 7. Update new customer's debt
    if data.customer_id:
        new_customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
        if new_customer and debt_amount > 0:
            new_customer.current_debt = Decimal(str(new_customer.current_debt or 0)) + debt_amount
    
    # 8. Track edit
    sale.updated_by_id = current_user.id
    sale.edit_reason = edit_reason
    
    db.commit()
    
    return {
        "success": True,
        "message": "Sotuv to'liq tahrirlandi",
        "data": {
            "id": sale.id,
            "sale_number": sale.sale_number,
            "total_amount": float(sale.total_amount),
            "paid_amount": float(sale.paid_amount),
            "debt_amount": float(sale.debt_amount),
            "items_count": len(new_items)
        }
    }


@router.get(
    "/{sale_id}/receipt",
    summary="Chek ma'lumotlari"
)
async def get_receipt(
    sale_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get receipt data for printing."""
    service = SaleService(db)
    sale = service.get_sale_by_id(sale_id)
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sotuv topilmadi")
    
    # Get company info from settings (simplified)
    company_name = "G'ayrat Stroy House"
    company_address = "Toshkent sh."
    company_phone = "+998 90 123 45 67"
    
    items = [{
        "name": item.product.name,
        "quantity": float(item.quantity),
        "uom": item.uom.symbol,
        "price": float(item.unit_price),
        "total": float(item.total_price)
    } for item in sale.items]
    
    # Calculate change
    total_paid = sum(p.amount for p in sale.payments)
    change = max(Decimal("0"), total_paid - sale.total_amount)
    
    return {
        "success": True,
        "data": {
            "sale_number": sale.sale_number,
            "sale_date": sale.created_at.isoformat(),
            "company_name": company_name,
            "company_address": company_address,
            "company_phone": company_phone,
            "customer_name": sale.customer.name if sale.customer else "Noma'lum mijoz",
            "customer_phone": sale.customer.phone if sale.customer else None,
            "seller_name": f"{sale.seller.first_name} {sale.seller.last_name}",
            "items": items,
            "subtotal": float(sale.subtotal),
            "discount_amount": float(sale.discount_amount),
            "discount_percent": float(sale.discount_percent),
            "total_amount": float(sale.total_amount),
            "paid_amount": float(sale.paid_amount),
            "debt_amount": float(sale.debt_amount),
            "change_amount": float(change),
            "payment_type": sale.payment_type.value if sale.payment_type else "MIXED",
            "thank_you_message": "Xaridingiz uchun rahmat!"
        }
    }
