"""
SMS router - SMS sending and testing endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from database.models import User, PermissionType, Customer
from core.dependencies import get_current_active_user, PermissionChecker
from services.sms import SMSService
from utils.helpers import get_tashkent_datetime_str


router = APIRouter()


class SMSSendRequest(BaseModel):
    """SMS send request."""
    phone: str
    message: str


class BulkSMSRequest(BaseModel):
    """Bulk SMS request."""
    message: str
    customer_type: Optional[str] = None  # VIP, REGULAR, all
    has_debt: Optional[bool] = None


@router.post(
    "/send",
    summary="SMS yuborish",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_EDIT]))]
)
async def send_sms(
    data: SMSSendRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send SMS to phone number."""
    service = SMSService(db)
    success, message = service.send_sms(
        phone=data.phone,
        message=data.message,
        reference_type="manual",
        reference_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}


@router.post(
    "/send-to-customer/{customer_id}",
    summary="Mijozga SMS yuborish",
    dependencies=[Depends(PermissionChecker([PermissionType.CUSTOMER_EDIT]))]
)
async def send_sms_to_customer(
    customer_id: int,
    data: SMSSendRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send SMS to specific customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Mijoz topilmadi")
    
    service = SMSService(db)
    
    # Replace placeholders
    message = data.message.format(customer_name=customer.name)
    
    success, result_message = service.send_sms(
        phone=customer.phone,
        message=message,
        reference_type="customer",
        reference_id=customer_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=result_message)
    
    return {"success": True, "message": result_message}


@router.post(
    "/debt-reminder/{customer_id}",
    summary="Qarz eslatmasi yuborish",
    dependencies=[Depends(PermissionChecker([PermissionType.CUSTOMER_EDIT]))]
)
async def send_debt_reminder(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send debt reminder SMS to customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Mijoz topilmadi")
    
    service = SMSService(db)
    success, message = service.send_debt_reminder(customer)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}


@router.post(
    "/bulk",
    summary="Ommaviy SMS yuborish",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_EDIT]))]
)
async def send_bulk_sms(
    data: BulkSMSRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send bulk SMS to customers."""
    # Query customers
    query = db.query(Customer).filter(
        Customer.is_deleted == False,
        Customer.sms_enabled == True,
        Customer.phone != None
    )
    
    if data.customer_type and data.customer_type != "all":
        query = query.filter(Customer.customer_type == data.customer_type)
    
    if data.has_debt is True:
        query = query.filter(Customer.current_debt > 0)
    elif data.has_debt is False:
        query = query.filter(Customer.current_debt == 0)
    
    customers = query.all()
    
    if not customers:
        raise HTTPException(status_code=400, detail="Hech qanday mijoz topilmadi")
    
    service = SMSService(db)
    success_count, failed_count = service.send_bulk_sms(customers, data.message)
    
    return {
        "success": True,
        "message": f"SMS yuborildi: {success_count} muvaffaqiyatli, {failed_count} xato",
        "success_count": success_count,
        "failed_count": failed_count
    }


@router.get(
    "/balance",
    summary="SMS balans"
)
async def get_sms_balance(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get SMS balance."""
    service = SMSService(db)
    balance = service.get_balance()
    
    return {
        "success": True,
        "balance": balance,
        "is_test_mode": service.is_test_mode
    }


@router.get(
    "/logs",
    summary="SMS tarixi"
)
async def get_sms_logs(
    phone: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get SMS sending logs."""
    service = SMSService(db)
    logs = service.get_sms_logs(phone=phone, status=status, limit=limit)
    
    data = [{
        "id": log.id,
        "phone": log.phone_number,
        "message": log.message[:50] + "..." if len(log.message) > 50 else log.message,
        "status": log.status,
        "reference_type": log.reference_type,
        "reference_id": log.reference_id,
        "sent_at": log.sent_at,
        "error_message": log.error_message,
        "created_at": log.created_at.isoformat()
    } for log in logs]
    
    return {"success": True, "data": data, "count": len(data)}


@router.get(
    "/test",
    summary="SMS test (terminalda log)"
)
async def test_sms(
    phone: str = Query(..., description="Test telefon raqami"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Test SMS sending.
    In test mode, SMS is logged to console instead of sending.
    """
    service = SMSService(db)
    
    test_message = f"Test SMS. Sana: {get_tashkent_datetime_str()}"
    
    success, message = service.send_sms(
        phone=phone,
        message=test_message,
        reference_type="test",
        reference_id=None
    )
    
    return {
        "success": success,
        "message": message,
        "is_test_mode": service.is_test_mode,
        "note": "Test mode'da SMS terminalga log qilinadi" if service.is_test_mode else "SMS yuborildi"
    }
