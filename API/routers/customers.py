"""
Customers router - CRUD operations and debt management.
"""

from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from database.models import User, PermissionType
from core.dependencies import get_current_active_user, PermissionChecker
from schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse,
    CustomerSearchParams, CustomerDebtListResponse, CustomerPaymentRequest,
    CustomerAdvanceRequest, VIPCredentialsCreate
)
from schemas.base import SuccessResponse, DeleteResponse
from services.customer import CustomerService
from services.telegram_notifier import send_payment_notification_sync
from utils.helpers import get_tashkent_now


router = APIRouter()


@router.get(
    "",
    response_model=CustomerListResponse,
    summary="Mijozlar ro'yxati"
)
async def get_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    customer_type: Optional[str] = None,
    has_debt: Optional[bool] = None,
    is_active: bool = True,
    manager_id: Optional[int] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated customers list."""
    service = CustomerService(db)
    
    params = CustomerSearchParams(
        q=q,
        customer_type=customer_type,
        has_debt=has_debt,
        is_active=is_active,
        manager_id=manager_id,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    customers, total = service.get_customers(page, per_page, params)
    
    data = [{
        "id": c.id,
        "name": c.name,
        "company_name": c.company_name,
        "phone": c.phone,
        "phone_secondary": c.phone_secondary,
        "telegram_id": c.telegram_id,
        "email": c.email,
        "address": c.address,
        "customer_type": c.customer_type.name if c.customer_type else "REGULAR",
        "credit_limit": c.credit_limit,
        "current_debt": c.current_debt,
        "advance_balance": c.advance_balance,
        "total_purchases": c.total_purchases,
        "is_active": c.is_active,
        "manager_id": c.manager_id,
        "manager_name": c.manager.full_name if c.manager else None
    } for c in customers]
    
    return CustomerListResponse(
        data=data,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get(
    "/debtors",
    summary="Qarzdorlar ro'yxati"
)
async def get_debtors(
    min_debt: Optional[Decimal] = None,
    seller_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all customers with debt. If seller_id is provided, returns only that seller's customers."""
    service = CustomerService(db)
    debtors = service.get_debtors(min_debt, manager_id=seller_id)
    total_debt = service.get_total_debt(manager_id=seller_id)
    
    data = [{
        "id": c.id,
        "name": c.name,
        "phone": c.phone,
        "company_name": c.company_name,
        "current_debt": c.current_debt,
        "credit_limit": c.credit_limit,
        "last_purchase_date": c.last_purchase_date.isoformat() if c.last_purchase_date else None
    } for c in debtors]
    
    return {
        "success": True,
        "data": data,
        "total_debt": total_debt,
        "debtors_count": len(debtors)
    }


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Mijoz ma'lumotlari"
)
async def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get customer by ID."""
    service = CustomerService(db)
    customer = service.get_customer_by_id(customer_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Mijoz topilmadi")
    
    return CustomerResponse.model_validate(customer)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Mijoz yaratish",
    dependencies=[Depends(PermissionChecker([PermissionType.CUSTOMER_CREATE]))]
)
async def create_customer(
    data: CustomerCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new customer."""
    service = CustomerService(db)
    customer, message = service.create_customer(data, current_user.id)
    
    if not customer:
        raise HTTPException(status_code=400, detail=message)
    
    return CustomerResponse.model_validate(customer)


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Mijozni yangilash",
    dependencies=[Depends(PermissionChecker([PermissionType.CUSTOMER_EDIT]))]
)
async def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update customer."""
    service = CustomerService(db)
    customer, message = service.update_customer(customer_id, data, current_user.id)
    
    if not customer:
        raise HTTPException(status_code=400, detail=message)
    
    return CustomerResponse.model_validate(customer)


@router.delete(
    "/{customer_id}",
    response_model=DeleteResponse,
    summary="Mijozni o'chirish",
    dependencies=[Depends(PermissionChecker([PermissionType.CUSTOMER_DELETE]))]
)
async def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete customer."""
    service = CustomerService(db)
    success, message = service.delete_customer(customer_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return DeleteResponse(id=customer_id, message=message)


# ==================== DEBT MANAGEMENT ====================

@router.get(
    "/{customer_id}/payments",
    summary="Mijoz to'lovlari tarixi"
)
async def get_customer_payments(
    customer_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get customer payment history."""
    service = CustomerService(db)
    
    customer = service.get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Mijoz topilmadi")
    
    # Get debt records that are PAYMENT type
    records, total = service.get_debt_history(customer_id, page, per_page)
    
    # Filter only payment records
    payments = [r for r in records if r.transaction_type in ['PAYMENT', 'payment', 'DEBT_PAYMENT']]
    
    data = [{
        "id": r.id,
        "transaction_type": r.transaction_type,
        "amount": abs(r.amount),
        "payment_type": r.reference_type.upper() if r.reference_type else "CASH",
        "description": r.description,
        "created_at": r.created_at.isoformat()
    } for r in payments]
    
    return {
        "success": True,
        "data": data,
        "total": len(payments)
    }


@router.get(
    "/{customer_id}/debt-history",
    summary="Mijoz qarz tarixi"
)
async def get_customer_debt_history(
    customer_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get customer debt transaction history."""
    service = CustomerService(db)
    
    customer = service.get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Mijoz topilmadi")
    
    records, total = service.get_debt_history(customer_id, page, per_page)
    
    data = [{
        "id": r.id,
        "transaction_type": r.transaction_type,
        "amount": r.amount,
        "balance_before": r.balance_before,
        "balance_after": r.balance_after,
        "reference_type": r.reference_type,
        "reference_id": r.reference_id,
        "description": r.description,
        "created_at": r.created_at.isoformat()
    } for r in records]
    
    return {
        "success": True,
        "data": data,
        "total": total,
        "current_debt": customer.current_debt,
        "advance_balance": customer.advance_balance
    }


@router.post(
    "/{customer_id}/pay-debt",
    summary="Qarz to'lash",
    dependencies=[Depends(PermissionChecker([PermissionType.PAYMENT_CREATE]))]
)
async def pay_customer_debt(
    customer_id: int,
    data: CustomerPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Record debt payment from customer."""
    service = CustomerService(db)
    
    # Get customer before payment
    customer_before = service.get_customer_by_id(customer_id)
    if not customer_before:
        raise HTTPException(status_code=404, detail="Mijoz topilmadi")
    
    previous_debt = float(customer_before.current_debt) if customer_before else 0
    
    success, message, change = service.pay_debt(
        customer_id,
        data.amount,
        data.payment_type,
        data.description,
        current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    customer = service.get_customer_by_id(customer_id)
    
    # Send Telegram notification for debt payment
    try:
        operator_name = f"{current_user.first_name} {current_user.last_name}"
        
        send_payment_notification_sync(
            customer_telegram_id=customer.telegram_id if customer else None,
            customer_name=customer.name if customer else "Noma'lum",
            customer_phone=customer.phone if customer else "",
            customer_type=customer.customer_type.name if customer else "STANDARD",
            payment_date=get_tashkent_now(),
            payment_amount=float(data.amount),
            payment_type=data.payment_type.value if hasattr(data.payment_type, 'value') else str(data.payment_type),
            previous_debt=previous_debt,
            current_debt=float(customer.current_debt),
            operator_name=operator_name
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to send payment notification: {e}")
    
    return {
        "success": True,
        "message": message,
        "change_amount": change,
        "current_debt": customer.current_debt,
        "advance_balance": customer.advance_balance
    }


@router.post(
    "/{customer_id}/add-advance",
    summary="Avans qo'shish",
    dependencies=[Depends(PermissionChecker([PermissionType.PAYMENT_CREATE]))]
)
async def add_customer_advance(
    customer_id: int,
    data: CustomerAdvanceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add advance payment from customer."""
    service = CustomerService(db)
    
    success, message = service.add_advance(
        customer_id,
        data.amount,
        data.payment_type,
        data.description,
        current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    customer = service.get_customer_by_id(customer_id)
    
    return {
        "success": True,
        "message": message,
        "advance_balance": customer.advance_balance
    }


# ==================== VIP MANAGEMENT ====================

@router.post(
    "/{customer_id}/set-vip",
    summary="VIP hisob yaratish",
    dependencies=[Depends(PermissionChecker([PermissionType.CUSTOMER_EDIT]))]
)
async def set_vip_credentials(
    customer_id: int,
    data: VIPCredentialsCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Set VIP credentials for customer (login/password for personal cabinet)."""
    service = CustomerService(db)
    
    success, message = service.set_vip_credentials(
        customer_id,
        data.login,
        data.password,
        current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return SuccessResponse(message=message)
