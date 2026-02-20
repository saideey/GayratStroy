"""
Settings router - System configuration management.
"""

import os
import subprocess
import tempfile
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from database.models import User, PermissionType, SystemSetting
from core.dependencies import get_current_active_user, PermissionChecker
from utils.helpers import get_tashkent_time_str, get_tashkent_today


router = APIRouter()


class SettingResponse(BaseModel):
    """Setting response schema."""
    key: str
    value: Optional[str] = None
    value_type: str
    category: Optional[str] = None
    description: Optional[str] = None


class SettingUpdate(BaseModel):
    """Setting update schema."""
    value: str


class DirectorTelegramIdsUpdate(BaseModel):
    """Director Telegram IDs update schema."""
    telegram_ids: List[str]


class ExchangeRateResponse(BaseModel):
    """Exchange rate response."""
    usd_rate: Decimal
    updated_at: Optional[str] = None


class ExchangeRateUpdate(BaseModel):
    """Exchange rate update request."""
    usd_rate: Decimal


@router.get(
    "",
    summary="Barcha sozlamalar"
)
async def get_settings(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all settings, optionally filtered by category."""
    query = db.query(SystemSetting)

    if category:
        query = query.filter(SystemSetting.category == category)

    # Non-admins can only see public settings
    if current_user.role.role_type != "admin":
        query = query.filter(SystemSetting.is_public == True)

    settings = query.all()

    return {
        "success": True,
        "data": [{
            "key": s.key,
            "value": s.value,
            "value_type": s.value_type,
            "category": s.category,
            "description": s.description
        } for s in settings]
    }


@router.get(
    "/exchange-rate",
    response_model=ExchangeRateResponse,
    summary="Dollar kursi"
)
async def get_exchange_rate(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current USD exchange rate."""
    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "usd_exchange_rate"
    ).first()

    if not setting:
        # Create default if not exists
        setting = SystemSetting(
            key="usd_exchange_rate",
            value="12800",
            value_type="number",
            category="currency",
            description="1 USD = ? so'm",
            is_public=True,
            is_editable=True
        )
        db.add(setting)
        db.commit()

    return ExchangeRateResponse(
        usd_rate=Decimal(setting.value or "12800"),
        updated_at=setting.updated_at.isoformat() if setting.updated_at else None
    )


@router.put(
    "/exchange-rate",
    response_model=ExchangeRateResponse,
    summary="Dollar kursini yangilash",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def update_exchange_rate(
    data: ExchangeRateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update USD exchange rate."""
    if data.usd_rate <= 0:
        raise HTTPException(status_code=400, detail="Kurs 0 dan katta bo'lishi kerak")

    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "usd_exchange_rate"
    ).first()

    if not setting:
        setting = SystemSetting(
            key="usd_exchange_rate",
            value_type="number",
            category="currency",
            description="1 USD = ? so'm",
            is_public=True,
            is_editable=True
        )
        db.add(setting)

    setting.value = str(data.usd_rate)
    db.commit()
    db.refresh(setting)

    return ExchangeRateResponse(
        usd_rate=Decimal(setting.value),
        updated_at=setting.updated_at.isoformat() if setting.updated_at else None
    )


@router.get(
    "/company-phones",
    summary="Kompaniya telefon raqamlari"
)
async def get_company_phones(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get company phone numbers for receipts."""
    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "company_phones"
    ).first()

    if not setting or not setting.value:
        return {
            "success": True,
            "data": {
                "phone1": "+998 XX XXX XX XX",
                "phone2": ""
            }
        }

    import json
    try:
        phones = json.loads(setting.value)
    except:
        phones = {"phone1": "+998 XX XXX XX XX", "phone2": ""}

    return {
        "success": True,
        "data": phones
    }


@router.put(
    "/company-phones",
    summary="Kompaniya telefon raqamlarini yangilash",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def update_company_phones(
    phone1: str = "",
    phone2: str = "",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update company phone numbers for receipts."""
    import json

    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "company_phones"
    ).first()

    phones_data = json.dumps({"phone1": phone1, "phone2": phone2})

    if not setting:
        setting = SystemSetting(
            key="company_phones",
            value=phones_data,
            value_type="json",
            category="company",
            description="Kompaniya telefon raqamlari (chek uchun)",
            is_public=True,
            is_editable=True
        )
        db.add(setting)
    else:
        setting.value = phones_data

    db.commit()

    return {
        "success": True,
        "message": "Telefon raqamlari saqlandi",
        "data": {"phone1": phone1, "phone2": phone2}
    }


@router.get(
    "/telegram/directors",
    summary="Direktor Telegram ID lari"
)
async def get_director_telegram_ids(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get director Telegram IDs for notifications."""
    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "director_telegram_ids"
    ).first()

    if not setting or not setting.value:
        return {
            "success": True,
            "data": {
                "telegram_ids": []
            }
        }

    # Parse comma-separated IDs
    ids = [id.strip() for id in setting.value.split(",") if id.strip()]

    return {
        "success": True,
        "data": {
            "telegram_ids": ids
        }
    }


@router.put(
    "/telegram/directors",
    summary="Direktor Telegram ID larini yangilash",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def update_director_telegram_ids(
    data: DirectorTelegramIdsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update director Telegram IDs for notifications."""
    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "director_telegram_ids"
    ).first()

    if not setting:
        setting = SystemSetting(
            key="director_telegram_ids",
            value_type="text",
            category="telegram",
            description="Direktor Telegram ID lari (vergul bilan ajratilgan)",
            is_public=False,
            is_editable=True
        )
        db.add(setting)

    # Join IDs with comma
    setting.value = ",".join([id.strip() for id in data.telegram_ids if id.strip()])
    db.commit()
    db.refresh(setting)

    # Parse back for response
    ids = [id.strip() for id in setting.value.split(",") if id.strip()] if setting.value else []

    return {
        "success": True,
        "message": "Direktor Telegram ID lari yangilandi",
        "data": {
            "telegram_ids": ids
        }
    }


@router.post(
    "/telegram/test",
    summary="Test xabar yuborish",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def test_telegram_notification(
    telegram_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send test message to verify Telegram ID."""
    import httpx
    import os

    bot_url = os.getenv("TELEGRAM_BOT_URL", "http://telegram_bot:8081")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{bot_url}/test",
                json={
                    "chat_id": telegram_id,
                    "message": f"🔔 Test xabar\n\nSozlamalar tekshiruvi muvaffaqiyatli!\n\nYuboruvchi: {current_user.first_name} {current_user.last_name}"
                }
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": result.get("success", False),
                    "message": "Test xabar yuborildi" if result.get("success") else "Xabar yuborilmadi"
                }
            else:
                return {
                    "success": False,
                    "message": f"Bot xatosi: {response.status_code}"
                }
    except httpx.ConnectError:
        return {
            "success": False,
            "message": "Telegram Bot servisi ishlamayapti"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@router.get(
    "/{key}",
    summary="Bitta sozlama"
)
async def get_setting(
    key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get setting by key."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()

    if not setting:
        raise HTTPException(status_code=404, detail="Sozlama topilmadi")

    # Check access
    if not setting.is_public and current_user.role.role_type != "admin":
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    return {
        "success": True,
        "data": {
            "key": setting.key,
            "value": setting.get_typed_value(),
            "value_type": setting.value_type,
            "category": setting.category,
            "description": setting.description
        }
    }


@router.put(
    "/{key}",
    summary="Sozlamani yangilash",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def update_setting(
    key: str,
    data: SettingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update setting value."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()

    if not setting:
        raise HTTPException(status_code=404, detail="Sozlama topilmadi")

    if not setting.is_editable:
        raise HTTPException(status_code=400, detail="Bu sozlamani o'zgartirib bo'lmaydi")

    setting.value = data.value
    db.commit()

    return {
        "success": True,
        "message": "Sozlama yangilandi",
        "data": {
            "key": setting.key,
            "value": setting.get_typed_value()
        }
    }


# ============ TELEGRAM GROUP DAILY REPORT SETTINGS ============

class TelegramGroupSettings(BaseModel):
    """Telegram group settings for daily reports."""
    group_chat_id: str
    report_time: str  # Format: "HH:MM" e.g., "19:00"
    is_enabled: bool = True


@router.get(
    "/telegram/group-settings",
    summary="Telegram guruh sozlamalari"
)
async def get_telegram_group_settings(
    db: Session = Depends(get_db)
):
    """Get Telegram group settings for daily reports (public for scheduler)."""
    # Get group chat ID
    group_setting = db.query(SystemSetting).filter(
        SystemSetting.key == "telegram_group_chat_id"
    ).first()

    # Get report time
    time_setting = db.query(SystemSetting).filter(
        SystemSetting.key == "daily_report_time"
    ).first()

    # Get enabled status
    enabled_setting = db.query(SystemSetting).filter(
        SystemSetting.key == "daily_report_enabled"
    ).first()

    return {
        "success": True,
        "data": {
            "group_chat_id": group_setting.value if group_setting else "",
            "report_time": time_setting.value if time_setting else "19:00",
            "is_enabled": enabled_setting.value == "true" if enabled_setting else False
        }
    }


@router.put(
    "/telegram/group-settings",
    summary="Telegram guruh sozlamalarini yangilash",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def update_telegram_group_settings(
    data: TelegramGroupSettings,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update Telegram group settings for daily reports."""

    try:
        # Update or create group chat ID
        group_setting = db.query(SystemSetting).filter(
            SystemSetting.key == "telegram_group_chat_id"
        ).first()
        if not group_setting:
            group_setting = SystemSetting(
                key="telegram_group_chat_id",
                value_type="text",
                category="telegram",
                description="Kunlik hisobot yuboriladigan guruh ID si",
                is_public=False,
                is_editable=True
            )
            db.add(group_setting)
        group_setting.value = data.group_chat_id

        # Update or create report time
        time_setting = db.query(SystemSetting).filter(
            SystemSetting.key == "daily_report_time"
        ).first()
        if not time_setting:
            time_setting = SystemSetting(
                key="daily_report_time",
                value_type="text",
                category="telegram",
                description="Kunlik hisobot yuborish vaqti (HH:MM)",
                is_public=False,
                is_editable=True
            )
            db.add(time_setting)
        time_setting.value = data.report_time

        # Update or create enabled status
        enabled_setting = db.query(SystemSetting).filter(
            SystemSetting.key == "daily_report_enabled"
        ).first()
        if not enabled_setting:
            enabled_setting = SystemSetting(
                key="daily_report_enabled",
                value_type="boolean",
                category="telegram",
                description="Kunlik hisobot yuborish yoqilgan",
                is_public=False,
                is_editable=True
            )
            db.add(enabled_setting)
        enabled_setting.value = "true" if data.is_enabled else "false"

        # Flush and commit
        db.flush()
        db.commit()

        return {
            "success": True,
            "message": "Telegram guruh sozlamalari yangilandi",
            "data": {
                "group_chat_id": data.group_chat_id,
                "report_time": data.report_time,
                "is_enabled": data.is_enabled
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Saqlashda xatolik: {str(e)}")


@router.post(
    "/telegram/send-daily-report",
    summary="Kunlik hisobotni hozir yuborish",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def send_daily_report_now(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send daily report with Excel to Telegram group immediately."""
    import httpx
    import os
    from datetime import date
    from sqlalchemy import func
    from database.models import Sale, SaleItem, Customer, User as UserModel, Product, Stock, UnitOfMeasure, Payment

    # Get group chat ID
    group_setting = db.query(SystemSetting).filter(
        SystemSetting.key == "telegram_group_chat_id"
    ).first()

    if not group_setting or not group_setting.value:
        raise HTTPException(status_code=400, detail="Telegram guruh ID si sozlanmagan")

    group_chat_id = group_setting.value
    today = date.today()

    # ===== COLLECT ALL DATA =====

    # Today's sales
    today_sales = db.query(Sale).filter(
        Sale.sale_date == today,
        Sale.is_cancelled == False
    ).all()

    total_sales_count = len(today_sales)
    total_amount = sum(float(s.total_amount or 0) for s in today_sales)
    total_paid = sum(float(s.paid_amount or 0) for s in today_sales)
    total_debt = sum(float(s.debt_amount or 0) for s in today_sales)
    total_discount = sum(float(s.discount_amount or 0) for s in today_sales)

    # Payment breakdown
    cash_amount = 0
    card_amount = 0
    transfer_amount = 0

    for sale in today_sales:
        if sale.paid_amount and float(sale.paid_amount) > 0 and sale.payment_type:
            pt = sale.payment_type.value if hasattr(sale.payment_type, 'value') else str(sale.payment_type)
            if pt == 'cash':
                cash_amount += float(sale.paid_amount)
            elif pt == 'card':
                card_amount += float(sale.paid_amount)
            elif pt == 'transfer':
                transfer_amount += float(sale.paid_amount)

    # Cashiers stats
    cashiers_stats = db.query(
        UserModel.id,
        UserModel.first_name,
        UserModel.last_name,
        func.count(Sale.id).label('sales_count'),
        func.coalesce(func.sum(Sale.total_amount), 0).label('total_amount'),
        func.coalesce(func.sum(Sale.paid_amount), 0).label('paid_amount'),
        func.coalesce(func.sum(Sale.debt_amount), 0).label('debt_amount')
    ).join(Sale, Sale.seller_id == UserModel.id)\
     .filter(
        Sale.sale_date == today,
        Sale.is_cancelled == False
    ).group_by(UserModel.id, UserModel.first_name, UserModel.last_name).all()

    cashiers = []
    for c in cashiers_stats:
        cashiers.append({
            "name": f"{c.first_name} {c.last_name}",
            "sales_count": c.sales_count,
            "total_amount": float(c.total_amount or 0),
            "paid_amount": float(c.paid_amount or 0),
            "debt_amount": float(c.debt_amount or 0)
        })

    # Today's debtors
    today_debtors = db.query(
        Customer.name,
        Customer.phone,
        func.coalesce(func.sum(Sale.debt_amount), 0).label('debt_amount')
    ).join(Sale, Sale.customer_id == Customer.id)\
     .filter(
        Sale.sale_date == today,
        Sale.debt_amount > 0,
        Sale.is_cancelled == False
    ).group_by(Customer.id, Customer.name, Customer.phone)\
     .order_by(func.sum(Sale.debt_amount).desc()).all()

    debtors = []
    for d in today_debtors:
        debtors.append({
            "name": d.name,
            "phone": d.phone or "",
            "debt_amount": float(d.debt_amount or 0)
        })

    # Total debt
    total_all_debt = db.query(func.coalesce(func.sum(Customer.current_debt), 0)).scalar() or 0

    # Sold products
    sold_products = db.query(
        Product.name,
        UnitOfMeasure.symbol,
        func.sum(SaleItem.quantity).label('qty'),
        func.sum(SaleItem.total_price).label('total')
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .join(UnitOfMeasure, UnitOfMeasure.id == SaleItem.uom_id)\
     .filter(
        Sale.sale_date == today,
        Sale.is_cancelled == False
    ).group_by(Product.id, Product.name, UnitOfMeasure.symbol)\
     .order_by(func.sum(SaleItem.total_price).desc()).all()

    products = []
    for p in sold_products:
        products.append({
            "name": p.name,
            "quantity": float(p.qty or 0),
            "uom": p.symbol,
            "total": float(p.total or 0)
        })

    # Low stock
    low_stock_items = db.query(Stock).join(Product).filter(
        Stock.quantity <= 10,
        Stock.quantity > 0
    ).all()

    low_stock = []
    for item in low_stock_items:
        try:
            low_stock.append({
                "name": item.product.name,
                "quantity": float(item.quantity or 0),
                "uom": item.product.base_uom.symbol if item.product.base_uom else ""
            })
        except:
            pass

    # ===== ALL DEBTORS WITH FULL DETAILS =====
    all_debtors_list = []

    # Get all customers with debt
    customers_with_debt = db.query(Customer).filter(
        Customer.current_debt > 0
    ).order_by(Customer.current_debt.desc()).all()

    for customer in customers_with_debt:
        # Get customer's unpaid sales (debt sales)
        customer_sales = db.query(Sale).filter(
            Sale.customer_id == customer.id,
            Sale.debt_amount > 0,
            Sale.is_cancelled == False
        ).order_by(Sale.sale_date.desc(), Sale.created_at.desc()).all()

        # Get customer's payments
        customer_payments = db.query(Payment).filter(
            Payment.customer_id == customer.id
        ).order_by(Payment.payment_date.desc()).limit(10).all()

        # Build sales list
        sales_list = []
        for sale in customer_sales[:20]:  # Last 20 debt sales
            # Get items for this sale
            sale_items = []
            for item in sale.items:
                sale_items.append({
                    "product": item.product.name if item.product else "?",
                    "quantity": float(item.quantity or 0),
                    "uom": item.uom.symbol if item.uom else "",
                    "price": float(item.unit_price or 0),
                    "total": float(item.total_price or 0)
                })

            sales_list.append({
                "sale_number": sale.sale_number,
                "date": sale.sale_date.strftime('%d.%m.%Y') if sale.sale_date else "",
                "time": sale.created_at.strftime('%H:%M') if sale.created_at else "",
                "total_amount": float(sale.total_amount or 0),
                "paid_amount": float(sale.paid_amount or 0),
                "debt_amount": float(sale.debt_amount or 0),
                "items": sale_items
            })

        # Build payments list
        payments_list = []
        for payment in customer_payments:
            payments_list.append({
                "date": payment.payment_date.strftime('%d.%m.%Y') if payment.payment_date else "",
                "amount": float(payment.amount or 0),
                "payment_type": payment.payment_type.value if payment.payment_type else "cash",
                "notes": payment.notes or ""
            })

        all_debtors_list.append({
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone or "",
            "total_debt": float(customer.current_debt or 0),
            "sales": sales_list,
            "payments": payments_list,
            "sales_count": len(customer_sales)
        })

    # Build report data
    report_data = {
        "date": today.isoformat(),
        "total_sales_count": total_sales_count,
        "total_amount": total_amount,
        "total_paid": total_paid,
        "total_debt": total_debt,
        "total_discount": total_discount,
        "cash_amount": cash_amount,
        "card_amount": card_amount,
        "transfer_amount": transfer_amount,
        "total_all_debt": float(total_all_debt),
        "cashiers": cashiers,
        "debtors": debtors,
        "products": products,
        "low_stock": low_stock,
        "all_debtors": all_debtors_list
    }

    # ===== SEND TO TELEGRAM BOT =====

    bot_url = os.getenv("TELEGRAM_BOT_URL", "http://telegram_bot:8081")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{bot_url}/send-daily-report-excel",
                json={
                    "chat_id": group_chat_id,
                    "report_data": report_data
                }
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": result.get("success", False),
                    "message": "Kunlik hisobot Excel bilan yuborildi" if result.get("success") else "Hisobot yuborilmadi"
                }
            else:
                return {
                    "success": False,
                    "message": f"Bot xatosi: {response.status_code}"
                }
    except httpx.ConnectError:
        return {
            "success": False,
            "message": "Telegram Bot servisi ishlamayapti"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@router.post(
    "/telegram/send-daily-report-internal",
    summary="Kunlik hisobotni scheduler orqali yuborish (ichki)",
    include_in_schema=False
)
async def send_daily_report_internal(
    db: Session = Depends(get_db)
):
    """
    Internal endpoint for scheduler to send daily report without authentication.
    This should only be accessible from within the Docker network.
    """
    import httpx
    import os
    from datetime import date
    from sqlalchemy import func
    from database.models import Sale, SaleItem, Customer, User as UserModel, Product, Stock, UnitOfMeasure

    # Get group chat ID
    group_setting = db.query(SystemSetting).filter(
        SystemSetting.key == "telegram_group_chat_id"
    ).first()

    if not group_setting or not group_setting.value:
        return {"success": False, "message": "Telegram guruh ID si sozlanmagan"}

    group_chat_id = group_setting.value
    today = date.today()

    def format_money(amount):
        return f"{float(amount or 0):,.0f}".replace(",", " ")

    # Today's sales
    today_sales = db.query(Sale).filter(
        Sale.sale_date == today,
        Sale.is_cancelled == False
    ).all()

    total_sales_count = len(today_sales)
    total_amount = sum(float(s.total_amount or 0) for s in today_sales)
    total_paid = sum(float(s.paid_amount or 0) for s in today_sales)
    total_debt = sum(float(s.debt_amount or 0) for s in today_sales)
    total_discount = sum(float(s.discount_amount or 0) for s in today_sales)

    # Payment breakdown
    cash_amount = 0
    card_amount = 0
    transfer_amount = 0

    for sale in today_sales:
        if sale.paid_amount and float(sale.paid_amount) > 0 and sale.payment_type:
            pt = sale.payment_type.value if hasattr(sale.payment_type, 'value') else str(sale.payment_type)
            if pt == 'cash':
                cash_amount += float(sale.paid_amount)
            elif pt == 'card':
                card_amount += float(sale.paid_amount)
            elif pt == 'transfer':
                transfer_amount += float(sale.paid_amount)

    # Cashiers stats
    cashiers_stats = db.query(
        UserModel.id,
        UserModel.first_name,
        UserModel.last_name,
        func.count(Sale.id).label('sales_count'),
        func.coalesce(func.sum(Sale.total_amount), 0).label('total_amount'),
        func.coalesce(func.sum(Sale.paid_amount), 0).label('paid_amount'),
        func.coalesce(func.sum(Sale.debt_amount), 0).label('debt_amount')
    ).join(Sale, Sale.seller_id == UserModel.id)\
     .filter(
        Sale.sale_date == today,
        Sale.is_cancelled == False
    ).group_by(UserModel.id, UserModel.first_name, UserModel.last_name).all()

    # Today's debtors
    today_debtors = db.query(
        Customer.name,
        Customer.phone,
        func.coalesce(func.sum(Sale.debt_amount), 0).label('debt_amount')
    ).join(Sale, Sale.customer_id == Customer.id)\
     .filter(
        Sale.sale_date == today,
        Sale.debt_amount > 0,
        Sale.is_cancelled == False
    ).group_by(Customer.id, Customer.name, Customer.phone)\
     .order_by(func.sum(Sale.debt_amount).desc()).all()

    # Total debt
    total_all_debt = db.query(func.coalesce(func.sum(Customer.current_debt), 0)).scalar() or 0

    # Sold products
    sold_products = db.query(
        Product.name,
        UnitOfMeasure.symbol,
        func.sum(SaleItem.quantity).label('qty'),
        func.sum(SaleItem.total_price).label('total')
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .join(UnitOfMeasure, UnitOfMeasure.id == SaleItem.uom_id)\
     .filter(
        Sale.sale_date == today,
        Sale.is_cancelled == False
    ).group_by(Product.id, Product.name, UnitOfMeasure.symbol)\
     .order_by(func.sum(SaleItem.total_price).desc()).all()

    # Low stock
    # Low stock
    low_stock = db.query(Stock).join(Product).filter(
        Stock.quantity <= 10,
        Stock.quantity > 0
    ).all()

    # Build report
    report_lines = [
        f"📊 <b>KUNLIK HISOBOT (Avtomatik)</b>",
        f"📅 <b>{today.strftime('%d.%m.%Y')}</b>",
        "",
        "═══════════════════════════",
        f"📦 <b>SOTUVLAR UMUMIY</b>",
        "═══════════════════════════",
        f"🛒 Sotuvlar soni: <b>{total_sales_count} ta</b>",
        f"💰 Jami summa: <b>{format_money(total_amount)} so'm</b>",
        f"✅ To'langan: <b>{format_money(total_paid)} so'm</b>",
        f"🔴 Bugungi qarz: <b>{format_money(total_debt)} so'm</b>",
    ]

    if total_discount > 0:
        report_lines.append(f"🏷 Chegirmalar: <b>{format_money(total_discount)} so'm</b>")

    report_lines.extend([
        "",
        "═══════════════════════════",
        f"💳 <b>TO'LOV TURLARI</b>",
        "═══════════════════════════",
        f"💵 Naqd pul: <b>{format_money(cash_amount)} so'm</b>",
        f"💳 Plastik karta: <b>{format_money(card_amount)} so'm</b>",
        f"🏦 O'tkazma: <b>{format_money(transfer_amount)} so'm</b>",
    ])

    if cashiers_stats:
        report_lines.extend([
            "",
            "═══════════════════════════",
            f"👥 <b>KASSIRLAR HISOBOTI</b>",
            "═══════════════════════════",
        ])
        for idx, c in enumerate(cashiers_stats, 1):
            name = f"{c.first_name} {c.last_name}"
            debt_text = f" (qarz: {format_money(c.debt_amount)})" if float(c.debt_amount or 0) > 0 else ""
            report_lines.append(
                f"{idx}. <b>{name}</b>\n"
                f"   📊 {c.sales_count} ta sotuv\n"
                f"   💰 {format_money(c.total_amount)} so'm{debt_text}"
            )

    if sold_products:
        report_lines.extend([
            "",
            "═══════════════════════════",
            f"📋 <b>SOTILGAN TOVARLAR</b>",
            "═══════════════════════════",
        ])
        for idx, p in enumerate(sold_products[:15], 1):
            report_lines.append(
                f"{idx}. {p.name}\n"
                f"   📦 {float(p.qty):.2f} {p.symbol} = {format_money(p.total)} so'm"
            )

    if today_debtors:
        report_lines.extend([
            "",
            "═══════════════════════════",
            f"📋 <b>BUGUNGI QARZDORLAR</b>",
            "═══════════════════════════",
        ])
        for idx, d in enumerate(today_debtors, 1):
            phone = f" ({d.phone})" if d.phone else ""
            report_lines.append(
                f"{idx}. {d.name}{phone}\n"
                f"   🔴 Qarz: <b>{format_money(d.debt_amount)} so'm</b>"
            )

    report_lines.extend([
        "",
        "═══════════════════════════",
        f"💰 <b>UMUMIY QARZ HOLATI</b>",
        "═══════════════════════════",
        f"📊 Jami qarzdorlik: <b>{format_money(total_all_debt)} so'm</b>",
    ])

    if low_stock:
        report_lines.extend([
            "",
            "═══════════════════════════",
            f"⚠️ <b>KAM QOLGAN TOVARLAR</b>",
            "═══════════════════════════",
        ])
        for item in low_stock[:10]:
            try:
                report_lines.append(
                    f"• {item.product.name}: <b>{float(item.quantity):.1f} {item.product.base_uom.symbol}</b>"
                )
            except:
                pass

    report_lines.extend([
        "",
        "═══════════════════════════",
        f"🕐 Hisobot vaqti: {get_tashkent_time_str()}",
        "═══════════════════════════",
        "",
        "🏭 <i>INTER PROFNASTIL</i>"
    ])

    report_message = "\n".join(report_lines)

    bot_url = os.getenv("TELEGRAM_BOT_URL", "http://telegram_bot:8081")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{bot_url}/send-daily-report",
                json={
                    "chat_id": group_chat_id,
                    "message": report_message
                }
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": result.get("success", False),
                    "message": "Kunlik hisobot yuborildi"
                }
    except Exception as e:
        return {"success": False, "message": str(e)}

    return {"success": False, "message": "Bot javob bermadi"}


@router.get(
    "/telegram/daily-report-data",
    summary="Kunlik hisobot ma'lumotlarini olish (scheduler uchun)",
    include_in_schema=False
)
async def get_daily_report_data(
    db: Session = Depends(get_db)
):
    """
    Get daily report data as JSON for scheduler/bot to generate Excel.
    This endpoint is used internally by the Telegram bot scheduler.
    """
    from datetime import date
    from sqlalchemy import func
    from database.models import Sale, SaleItem, Customer, User as UserModel, Product, Stock, UnitOfMeasure, Payment

    today = date.today()

    try:
        # Today's sales
        today_sales = db.query(Sale).filter(
            Sale.sale_date == today,
            Sale.is_cancelled == False
        ).all()

        total_sales_count = len(today_sales)
        total_amount = sum(float(s.total_amount or 0) for s in today_sales)
        total_paid = sum(float(s.paid_amount or 0) for s in today_sales)
        total_debt = sum(float(s.debt_amount or 0) for s in today_sales)
        total_discount = sum(float(s.discount_amount or 0) for s in today_sales)

        # Payment breakdown
        cash_amount = 0
        card_amount = 0
        transfer_amount = 0

        for sale in today_sales:
            if sale.paid_amount and float(sale.paid_amount) > 0 and sale.payment_type:
                pt = sale.payment_type.value if hasattr(sale.payment_type, 'value') else str(sale.payment_type)
                if pt == 'cash':
                    cash_amount += float(sale.paid_amount)
                elif pt == 'card':
                    card_amount += float(sale.paid_amount)
                elif pt == 'transfer':
                    transfer_amount += float(sale.paid_amount)

        # Cashiers stats
        cashiers_stats = db.query(
            UserModel.id,
            UserModel.first_name,
            UserModel.last_name,
            func.count(Sale.id).label('sales_count'),
            func.coalesce(func.sum(Sale.total_amount), 0).label('total_amount'),
            func.coalesce(func.sum(Sale.paid_amount), 0).label('paid_amount'),
            func.coalesce(func.sum(Sale.debt_amount), 0).label('debt_amount')
        ).join(Sale, Sale.seller_id == UserModel.id)\
         .filter(
            Sale.sale_date == today,
            Sale.is_cancelled == False
        ).group_by(UserModel.id, UserModel.first_name, UserModel.last_name).all()

        cashiers = []
        for c in cashiers_stats:
            cashiers.append({
                "name": f"{c.first_name} {c.last_name}",
                "sales_count": c.sales_count,
                "total_amount": float(c.total_amount or 0),
                "paid_amount": float(c.paid_amount or 0),
                "debt_amount": float(c.debt_amount or 0)
            })

        # Today's debtors
        today_debtors = db.query(
            Customer.name,
            Customer.phone,
            func.coalesce(func.sum(Sale.debt_amount), 0).label('debt_amount')
        ).join(Sale, Sale.customer_id == Customer.id)\
         .filter(
            Sale.sale_date == today,
            Sale.debt_amount > 0,
            Sale.is_cancelled == False
        ).group_by(Customer.id, Customer.name, Customer.phone)\
         .order_by(func.sum(Sale.debt_amount).desc()).all()

        debtors = []
        for d in today_debtors:
            debtors.append({
                "name": d.name,
                "phone": d.phone or "",
                "debt_amount": float(d.debt_amount or 0)
            })

        # Total debt
        total_all_debt = db.query(func.coalesce(func.sum(Customer.current_debt), 0)).scalar() or 0

        # Sold products today
        sold_products = db.query(
            Product.name,
            UnitOfMeasure.symbol,
            func.sum(SaleItem.quantity).label('qty'),
            func.sum(SaleItem.total_price).label('total')
        ).join(SaleItem, SaleItem.product_id == Product.id)\
         .join(Sale, Sale.id == SaleItem.sale_id)\
         .join(UnitOfMeasure, UnitOfMeasure.id == SaleItem.uom_id)\
         .filter(
            Sale.sale_date == today,
            Sale.is_cancelled == False
        ).group_by(Product.id, Product.name, UnitOfMeasure.symbol)\
         .order_by(func.sum(SaleItem.total_price).desc()).all()

        products = []
        for p in sold_products:
            products.append({
                "name": p.name,
                "quantity": float(p.qty or 0),
                "uom": p.symbol,
                "total": float(p.total or 0)
            })

        # Low stock items
        low_stock_items = db.query(Stock).join(Product).filter(
            Stock.quantity <= 10,
            Stock.quantity > 0
        ).all()

        low_stock = []
        for item in low_stock_items:
            try:
                low_stock.append({
                    "name": item.product.name,
                    "quantity": float(item.quantity or 0),
                    "uom": item.product.base_uom.symbol if item.product.base_uom else ""
                })
            except:
                pass

        # ===== ALL DEBTORS WITH FULL DETAILS =====
        all_debtors_list = []

        # Get all customers with debt
        customers_with_debt = db.query(Customer).filter(
            Customer.current_debt > 0
        ).order_by(Customer.current_debt.desc()).all()

        for customer in customers_with_debt:
            # Get customer's unpaid sales (debt sales)
            customer_sales = db.query(Sale).filter(
                Sale.customer_id == customer.id,
                Sale.debt_amount > 0,
                Sale.is_cancelled == False
            ).order_by(Sale.sale_date.desc(), Sale.created_at.desc()).all()

            # Get customer's payments
            customer_payments = db.query(Payment).filter(
                Payment.customer_id == customer.id
            ).order_by(Payment.payment_date.desc()).limit(10).all()

            # Build sales list
            sales_list = []
            for sale in customer_sales[:20]:  # Last 20 debt sales
                # Get items for this sale
                sale_items = []
                for item in sale.items:
                    sale_items.append({
                        "product": item.product.name if item.product else "?",
                        "quantity": float(item.quantity or 0),
                        "uom": item.uom.symbol if item.uom else "",
                        "price": float(item.unit_price or 0),
                        "total": float(item.total_price or 0)
                    })

                sales_list.append({
                    "sale_number": sale.sale_number,
                    "date": sale.sale_date.strftime('%d.%m.%Y') if sale.sale_date else "",
                    "time": sale.created_at.strftime('%H:%M') if sale.created_at else "",
                    "total_amount": float(sale.total_amount or 0),
                    "paid_amount": float(sale.paid_amount or 0),
                    "debt_amount": float(sale.debt_amount or 0),
                    "items": sale_items
                })

            # Build payments list
            payments_list = []
            for payment in customer_payments:
                payments_list.append({
                    "date": payment.payment_date.strftime('%d.%m.%Y') if payment.payment_date else "",
                    "amount": float(payment.amount or 0),
                    "payment_type": payment.payment_type.value if payment.payment_type else "cash",
                    "notes": payment.notes or ""
                })

            all_debtors_list.append({
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone or "",
                "total_debt": float(customer.current_debt or 0),
                "sales": sales_list,
                "payments": payments_list,
                "sales_count": len(customer_sales)
            })

        return {
            "success": True,
            "data": {
                "date": today.isoformat(),
                "total_sales_count": total_sales_count,
                "total_amount": total_amount,
                "total_paid": total_paid,
                "total_debt": total_debt,
                "total_discount": total_discount,
                "cash_amount": cash_amount,
                "card_amount": card_amount,
                "transfer_amount": transfer_amount,
                "total_all_debt": float(total_all_debt),
                "cashiers": cashiers,
                "debtors": debtors,
                "products": products,
                "low_stock": low_stock,
                "all_debtors": all_debtors_list
            }
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@router.get(
    "/database/backup",
    summary="Ma'lumotlar bazasini yuklab olish",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def download_database_backup(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download full PostgreSQL database backup.
    Creates a complete backup with all data (sales, customers, products, etc.)
    Filename format: DD.MM.YYYY.sql
    """

    # Get database connection info from DATABASE_URL or environment
    database_url = os.getenv("DATABASE_URL", "")

    if database_url:
        # Parse DATABASE_URL: postgresql://user:password@host:port/dbname
        # Example: postgresql://postgres:postgres@db:5432/metall_basa
        try:
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            db_host = parsed.hostname or "db"
            db_port = str(parsed.port or 5432)
            db_name = parsed.path.lstrip("/") or "metall_basa"
            db_user = parsed.username or "postgres"
            db_password = parsed.password or "postgres"
        except Exception:
            db_host = os.getenv("POSTGRES_HOST", "db")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            db_name = os.getenv("POSTGRES_DB", "metall_basa")
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    else:
        db_host = os.getenv("POSTGRES_HOST", "db")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "metall_basa")
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "postgres")

    # Generate filename with today's date (Tashkent time)
    today = get_tashkent_today()
    filename = f"{today.strftime('%d.%m.%Y')}.sql"

    # Create temporary file for backup
    temp_dir = tempfile.gettempdir()
    backup_path = os.path.join(temp_dir, filename)

    try:
        # Set password environment variable for pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password

        # Run pg_dump command
        cmd = [
            "pg_dump",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-F", "p",  # Plain text format
            "--no-owner",
            "--no-acl",
            "-f", backup_path
        ]

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Backup xatoligi: {result.stderr}"
            )

        # Check if file was created
        if not os.path.exists(backup_path):
            raise HTTPException(
                status_code=500,
                detail="Backup fayli yaratilmadi"
            )

        # Return file for download
        return FileResponse(
            path=backup_path,
            filename=filename,
            media_type="application/sql",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Backup vaqti tugadi (timeout)"
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="pg_dump topilmadi. PostgreSQL client o'rnatilganligini tekshiring."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backup xatoligi: {str(e)}"
        )