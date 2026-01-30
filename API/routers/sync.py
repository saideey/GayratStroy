"""
Sync router - Desktop app sinxronizatsiyasi uchun.
Handles push/pull operations for offline-first sync.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from database.models import User, Customer, CustomerDebt
from core.dependencies import get_current_active_user
from services.customer import CustomerService

router = APIRouter()


# ==================== SCHEMAS ====================

class SyncItem(BaseModel):
    """Single sync operation item."""
    action: str  # create, update, delete, pay_debt
    entity_type: str  # customer, payment
    payload: dict


class SyncPushRequest(BaseModel):
    """Push sync request with multiple items."""
    items: List[SyncItem]


class SyncPushResponse(BaseModel):
    """Push sync response."""
    success: bool
    processed: int
    failed: int
    errors: List[dict] = []


class SyncPullResponse(BaseModel):
    """Pull sync response."""
    success: bool
    data: List[dict]
    count: int
    sync_time: str


# ==================== ROUTES ====================

@router.post(
    "/push",
    response_model=SyncPushResponse,
    summary="Push local changes to server"
)
async def sync_push(
        request: SyncPushRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Receive batch of changes from desktop app.
    Process each item and return results.
    """
    service = CustomerService(db)
    processed = 0
    failed = 0
    errors = []

    for item in request.items:
        try:
            if item.entity_type == 'customer':
                if item.action == 'create':
                    # Create customer
                    from schemas.customer import CustomerCreate
                    data = CustomerCreate(**item.payload)
                    customer, msg = service.create_customer(data, current_user.id)
                    if customer:
                        processed += 1
                    else:
                        failed += 1
                        errors.append({
                            'action': item.action,
                            'entity_type': item.entity_type,
                            'error': msg
                        })

                elif item.action == 'update':
                    customer_id = item.payload.get('id')
                    if customer_id:
                        from schemas.customer import CustomerUpdate
                        update_data = {k: v for k, v in item.payload.items() if k != 'id'}
                        data = CustomerUpdate(**update_data)
                        customer, msg = service.update_customer(customer_id, data, current_user.id)
                        if customer:
                            processed += 1
                        else:
                            failed += 1
                            errors.append({
                                'action': item.action,
                                'entity_type': item.entity_type,
                                'error': msg
                            })
                    else:
                        failed += 1
                        errors.append({
                            'action': item.action,
                            'entity_type': item.entity_type,
                            'error': 'Customer ID required'
                        })

            elif item.entity_type == 'payment':
                if item.action == 'pay_debt':
                    customer_id = item.payload.get('customer_id')
                    amount = item.payload.get('amount')
                    payment_type = item.payload.get('payment_type', 'CASH')
                    description = item.payload.get('description')

                    if customer_id and amount:
                        success, msg, _ = service.pay_debt(
                            customer_id,
                            amount,
                            payment_type,
                            description,
                            current_user.id
                        )
                        if success:
                            processed += 1
                        else:
                            failed += 1
                            errors.append({
                                'action': item.action,
                                'entity_type': item.entity_type,
                                'error': msg
                            })
                    else:
                        failed += 1
                        errors.append({
                            'action': item.action,
                            'entity_type': item.entity_type,
                            'error': 'customer_id and amount required'
                        })

        except Exception as e:
            failed += 1
            errors.append({
                'action': item.action,
                'entity_type': item.entity_type,
                'error': str(e)
            })

    return SyncPushResponse(
        success=failed == 0,
        processed=processed,
        failed=failed,
        errors=errors
    )


@router.get(
    "/pull",
    response_model=SyncPullResponse,
    summary="Pull changes from server"
)
async def sync_pull(
        updated_since: Optional[str] = Query(None, description="ISO timestamp"),
        entity_type: Optional[str] = Query(None, description="customer, payment"),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Get all changes since given timestamp.
    Used for delta sync.
    """
    data = []

    # Parse timestamp
    since_dt = None
    if updated_since:
        try:
            since_dt = datetime.fromisoformat(updated_since.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format")

    # Get customers
    if not entity_type or entity_type == 'customer':
        query = db.query(Customer).filter(Customer.is_deleted == False)

        if since_dt:
            query = query.filter(Customer.updated_at > since_dt)

        customers = query.all()

        for c in customers:
            data.append({
                'entity_type': 'customer',
                'id': c.id,
                'name': c.name,
                'company_name': c.company_name,
                'phone': c.phone,
                'phone_secondary': c.phone_secondary,
                'address': c.address,
                'customer_type': c.customer_type.name if c.customer_type else 'REGULAR',
                'credit_limit': float(c.credit_limit or 0),
                'current_debt': float(c.current_debt or 0),
                'advance_balance': float(c.advance_balance or 0),
                'total_purchases': float(c.total_purchases or 0),
                'is_active': c.is_active,
                'updated_at': c.updated_at.isoformat() if c.updated_at else None
            })

    return SyncPullResponse(
        success=True,
        data=data,
        count=len(data),
        sync_time=datetime.utcnow().isoformat()
    )


@router.get(
    "/status",
    summary="Check sync status"
)
async def sync_status(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Get server status and last sync info.
    Can be used by desktop app to check connectivity.
    """
    service = CustomerService(db)
    total_customers = db.query(Customer).filter(Customer.is_deleted == False).count()
    total_debtors = db.query(Customer).filter(
        Customer.is_deleted == False,
        Customer.current_debt > 0
    ).count()
    total_debt = service.get_total_debt()

    return {
        'success': True,
        'server_time': datetime.utcnow().isoformat(),
        'stats': {
            'total_customers': total_customers,
            'total_debtors': total_debtors,
            'total_debt': float(total_debt or 0)
        }
    }