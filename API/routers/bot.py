"""
Bot Router - Telegram bot va WebApp uchun maxsus API endpointlar.

Bu router faqat telegram bot va WebApp ishlatadi.
Autentifikatsiya: telegram_id va initData orqali.

Endpoints:
  POST /bot/link-phone      - Telefon raqam orqali mijozni telegram_id bilan bog'lash
  GET  /bot/my-profile      - Mijoz profili (bot/WebApp uchun)
  GET  /bot/my-sales        - Mijozning sotuvlari ro'yxati
  GET  /bot/my-sales/{id}   - Bitta sotuv tafsiloti
  GET  /bot/my-debt         - Qarz holati va tarixi
  POST /bot/verify-webapp   - WebApp initData ni tekshirish va JWT qaytarish
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from database.models.customer import Customer, CustomerDebt
from database.models.sale import Sale, SaleItem, PaymentStatus, Payment
from database.models.product import Product
from database.models.settings import SystemSetting
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== DB DAN KOMPANIYA MA'LUMOTLARI =====

def get_company_setting(db: Session, key: str, default: str = "") -> str:
    """DB dagi system_settings jadvalidan qiymat olish."""
    try:
        row = db.query(SystemSetting).filter(
            SystemSetting.key == key
        ).first()
        if row and row.value:
            return row.value.strip()
    except Exception:
        pass
    return default


def get_company_info(db: Session) -> dict:
    """Kompaniya nomi va telefon raqamini DB dan olish."""
    return {
        "name": get_company_setting(db, "company_name", "G'ayrat Stroy House"),
        "phone": get_company_setting(db, "company_phone", ""),
    }


# ===== SCHEMAS =====

class LinkPhoneRequest(BaseModel):
    telegram_id: str
    phone: str          # Mijoz yuborgan telefon raqami
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class VerifyWebAppRequest(BaseModel):
    init_data: str      # Telegram WebApp.initData string


class LinkPhoneResponse(BaseModel):
    success: bool
    found: bool
    customer_name: Optional[str] = None
    customer_id: Optional[int] = None
    message: str


# ===== HELPERS =====

def normalize_phone(phone: str) -> str:
    """Telefon raqamni +998XXXXXXXXX formatga keltirish."""
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith("998") and len(digits) == 12:
        return f"+{digits}"
    if digits.startswith("8") and len(digits) == 11:
        return f"+7{digits[1:]}"  # Kazakhstan
    if len(digits) == 9:
        return f"+998{digits}"
    if len(digits) == 12 and not digits.startswith("998"):
        return f"+{digits}"
    return f"+{digits}" if not phone.startswith("+") else phone


def get_customer_by_telegram_id(telegram_id: str, db: Session) -> Optional[Customer]:
    """Telegram ID bo'yicha mijozni toping."""
    return db.query(Customer).filter(
        Customer.telegram_id == str(telegram_id),
        Customer.is_deleted == False,
        Customer.is_active == True
    ).first()


def get_customer_by_phone_normalized(phone: str, db: Session) -> Optional[Customer]:
    """Telefon raqam bo'yicha mijozni toping (turli formatlarni tekshiradi)."""
    normalized = normalize_phone(phone)
    
    # +998XXXXXXXXX
    customer = db.query(Customer).filter(
        Customer.is_deleted == False,
        Customer.is_active == True,
        Customer.phone == normalized
    ).first()
    if customer:
        return customer
    
    # Faqat raqamlar bilan qidirish (oxirgi 9 ta)
    digits_only = "".join(c for c in phone if c.isdigit())
    if len(digits_only) >= 9:
        last9 = digits_only[-9:]
        # DB dagi barcha mijozlar ichidan qidirish
        customers = db.query(Customer).filter(
            Customer.is_deleted == False,
            Customer.is_active == True
        ).all()
        for c in customers:
            db_digits = "".join(x for x in c.phone if x.isdigit())
            if db_digits.endswith(last9):
                return c
    
    return None


def verify_telegram_init_data(init_data: str, bot_token: str) -> Optional[dict]:
    """
    Telegram WebApp initData ni tekshirish.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        params = {}
        for item in init_data.split("&"):
            if "=" in item:
                k, v = item.split("=", 1)
                params[k] = v
        
        received_hash = params.pop("hash", None)
        if not received_hash:
            return None
        
        # Data-check-string yasash
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(params.items())
        )
        
        # HMAC-SHA256
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_hash, received_hash):
            return None
        
        # auth_date tekshirish (1 soatdan eski bo'lsa rad etish)
        auth_date = int(params.get("auth_date", 0))
        if datetime.now().timestamp() - auth_date > 3600:
            return None
        
        # user ma'lumotlarini parse qilish
        user_str = params.get("user", "{}")
        user = json.loads(user_str) if user_str else {}
        params["user_parsed"] = user
        
        return params
    except Exception as e:
        logger.error(f"initData verification error: {e}")
        return None


def get_customer_from_telegram_header(
    x_telegram_id: Optional[str],
    db: Session
) -> Customer:
    """Header dan telegram_id olish va mijozni topish."""
    if not x_telegram_id:
        raise HTTPException(status_code=401, detail="X-Telegram-Id header kerak")
    
    customer = get_customer_by_telegram_id(x_telegram_id, db)
    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Siz tizimda ro'yxatdan o'tmagan mijoz sifatida topilmadingiz. "
                   "Botda /start buyrug'ini bosing va telefon raqamingizni yuboring."
        )
    return customer


# ===== ENDPOINTS =====

@router.get("/company-info")
async def get_company_info_endpoint(db: Session = Depends(get_db)):
    """
    Kompaniya nomi va telefon raqami — autentifikatsiyasiz.
    Bot /start da va boshqa joylarda ishlatiladi.
    """
    company = get_company_info(db)
    return {
        "success": True,
        "data": {
            "name": company["name"],
            "phone": company["phone"],
        }
    }


@router.post("/link-phone", response_model=LinkPhoneResponse)
async def link_phone(
    data: LinkPhoneRequest,
    db: Session = Depends(get_db)
):
    """
    Mijoz telegram botda /start bosib telefon raqamini yuborganda chaqiriladi.
    Telefon raqam bo'yicha mijozni qidiradi va telegram_id ni bog'laydi.
    """
    # Avval bu telegram_id allaqachon bog'langanmi tekshir
    existing = get_customer_by_telegram_id(data.telegram_id, db)
    if existing:
        return LinkPhoneResponse(
            success=True,
            found=True,
            customer_name=existing.name,
            customer_id=existing.id,
            message=f"Xush kelibsiz, {existing.name}! Siz allaqachon ro'yxatdan o'tgansiz."
        )
    
    # Telefon raqam bo'yicha mijozni qidirish
    customer = get_customer_by_phone_normalized(data.phone, db)
    
    if not customer:
        # Mijoz topilmadi — DB dan kompaniya telefon raqamini olamiz
        company = get_company_info(db)
        contact_phone = company["phone"] or "do'konimiz"
        logger.info(f"Customer not found for phone: {data.phone}, telegram_id: {data.telegram_id}")
        return LinkPhoneResponse(
            success=False,
            found=False,
            message=(
                f"Afsuski, {data.phone} raqami bilan tizimda mijoz topilmadi.\n"
                f"Iltimos, {contact_phone} raqamiga murojaat qiling."
            )
        )
    
    # Telegram ID ni saqlash
    customer.telegram_id = str(data.telegram_id)
    db.commit()
    db.refresh(customer)
    
    logger.info(f"Linked telegram_id={data.telegram_id} to customer_id={customer.id} ({customer.name})")
    
    return LinkPhoneResponse(
        success=True,
        found=True,
        customer_name=customer.name,
        customer_id=customer.id,
        message=f"Xush kelibsiz, {customer.name}! Shaxsiy kabinetingizga kiring."
    )


@router.get("/my-profile")
async def get_my_profile(
    x_telegram_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Mijozning profili va umumiy statistika."""
    customer = get_customer_from_telegram_header(x_telegram_id, db)

    # So'nggi xarid sanasi
    last_sale = db.query(Sale).filter(
        Sale.customer_id == customer.id,
        Sale.is_cancelled == False
    ).order_by(desc(Sale.sale_date)).first()

    # Kompaniya ma'lumotlari DB dan
    company = get_company_info(db)

    return {
        "success": True,
        "data": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "customer_type": customer.customer_type.value if customer.customer_type else "regular",
            "current_debt": float(customer.current_debt or 0),
            "advance_balance": float(customer.advance_balance or 0),
            "total_purchases": float(customer.total_purchases or 0),
            "total_purchases_count": customer.total_purchases_count or 0,
            "personal_discount_percent": float(customer.personal_discount_percent or 0),
            "last_purchase_date": last_sale.sale_date.isoformat() if last_sale else None,
            "is_vip": customer.customer_type and customer.customer_type.value in ("vip", "wholesale", "contractor"),
            "company_name": company["name"],
            "company_phone": company["phone"],
        }
    }


@router.get("/my-sales")
async def get_my_sales(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    x_telegram_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Mijozning sotuvlari ro'yxati (sahifalash bilan)."""
    customer = get_customer_from_telegram_header(x_telegram_id, db)
    
    query = db.query(Sale).filter(
        Sale.customer_id == customer.id,
        Sale.is_cancelled == False
    ).order_by(desc(Sale.sale_date), desc(Sale.created_at))
    
    total = query.count()
    offset = (page - 1) * per_page
    sales = query.offset(offset).limit(per_page).all()
    
    sales_data = []
    for sale in sales:
        # To'lov holati
        if sale.payment_status == PaymentStatus.PAID:
            status_text = "To'liq to'langan"
            status_icon = "✅"
        elif sale.payment_status == PaymentStatus.PARTIAL:
            status_text = "Qisman to'langan"
            status_icon = "⚠️"
        else:
            status_text = "To'lanmagan"
            status_icon = "🔴"
        
        # Mahsulotlar (qisqacha) — product va uom relationship orqali
        items_list = list(sale.items)[:3]
        items_preview = []
        for item in items_list:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            uom_symbol = ""
            try:
                if item.uom:
                    uom_symbol = item.uom.symbol or ""
            except Exception:
                pass
            items_preview.append({
                "product_name": product.name if product else "Noma'lum",
                "quantity": float(item.quantity),
                "uom_symbol": uom_symbol,
                "total_price": float(item.total_price or 0),
            })

        total_items = sale.items.count() if hasattr(sale.items, 'count') else len(list(sale.items))
        
        sales_data.append({
            "id": sale.id,
            "sale_number": sale.sale_number,
            "sale_date": sale.sale_date.isoformat(),
            "total_amount": float(sale.total_amount or 0),
            "paid_amount": float(sale.paid_amount or 0),
            "debt_amount": float(sale.debt_amount or 0),
            "payment_status": sale.payment_status.value if sale.payment_status else "pending",
            "status_text": status_text,
            "status_icon": status_icon,
            "items_count": total_items,
            "items_preview": items_preview,
            "has_more_items": total_items > 3,
        })
    
    return {
        "success": True,
        "data": sales_data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/my-sales/{sale_id}")
async def get_sale_detail(
    sale_id: int,
    x_telegram_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Bitta sotuvning to'liq tafsiloti."""
    customer = get_customer_from_telegram_header(x_telegram_id, db)
    
    sale = db.query(Sale).filter(
        Sale.id == sale_id,
        Sale.customer_id == customer.id,
        Sale.is_cancelled == False
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sotuv topilmadi")
    
    # Barcha mahsulotlar — uom relationship orqali symbol olish
    items_data = []
    for item in sale.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        uom_symbol = ""
        try:
            if item.uom:
                uom_symbol = item.uom.symbol or ""
        except Exception:
            pass
        items_data.append({
            "product_name": product.name if product else "Noma'lum",
            "quantity": float(item.quantity),
            "uom_symbol": uom_symbol,
            "unit_price": float(item.unit_price or 0),
            "discount_amount": float(item.discount_amount or 0),
            "total_price": float(item.total_price or 0),
        })
    
    # To'lovlar tarixi (bu savdo uchun)
    payments_data = []
    try:
        payments = db.query(Payment).filter(
            Payment.sale_id == sale_id,
            Payment.is_cancelled == False
        ).order_by(Payment.payment_date).all()
        for p in payments:
            payment_type_map = {"cash": "Naqd", "card": "Karta", "transfer": "O'tkazma"}
            payments_data.append({
                "amount": float(p.amount or 0),
                "payment_type": payment_type_map.get(
                    p.payment_type.value if p.payment_type else "", "Noma'lum"
                ),
                "date": p.payment_date.isoformat() if p.payment_date else None,
                "notes": p.notes or "",
            })
    except Exception as e:
        logger.warning(f"Could not load payments for sale {sale_id}: {e}")
    
    status_map = {
        "paid":    "✅ To'liq to'langan",
        "partial": "⚠️ Qisman to'langan",
        "pending": "🔴 To'lanmagan",
    }
    status_val = sale.payment_status.value if sale.payment_status else "pending"

    # Kassir ismi seller relationship orqali
    operator_name = ""
    try:
        if sale.seller:
            first = getattr(sale.seller, "first_name", "") or ""
            last = getattr(sale.seller, "last_name", "") or ""
            operator_name = f"{first} {last}".strip() or getattr(sale.seller, "username", "") or ""
    except Exception:
        pass

    return {
        "success": True,
        "data": {
            "id": sale.id,
            "sale_number": sale.sale_number,
            "sale_date": sale.sale_date.isoformat(),
            "total_amount": float(sale.total_amount or 0),
            "paid_amount": float(sale.paid_amount or 0),
            "debt_amount": float(sale.debt_amount or 0),
            "discount_amount": float(sale.discount_amount or 0),
            "payment_status": status_val,
            "status_text": status_map.get(status_val, status_val),
            "items": items_data,
            "payments": payments_data,
            "operator_name": operator_name,
        }
    }


@router.get("/my-debt")
async def get_my_debt(
    x_telegram_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Mijozning qarz holati va to'lovlar tarixi."""
    customer = get_customer_from_telegram_header(x_telegram_id, db)
    
    # Qarz bo'lgan sotuvlar
    debt_sales = db.query(Sale).filter(
        Sale.customer_id == customer.id,
        Sale.is_cancelled == False,
        Sale.debt_amount > 0
    ).order_by(desc(Sale.sale_date)).all()
    
    debt_sales_data = []
    for sale in debt_sales:
        debt_sales_data.append({
            "id": sale.id,
            "sale_number": sale.sale_number,
            "sale_date": sale.sale_date.isoformat(),
            "total_amount": float(sale.total_amount or 0),
            "paid_amount": float(sale.paid_amount or 0),
            "debt_amount": float(sale.debt_amount or 0),
        })
    
    # To'lovlar tarixi (CustomerDebt jadvali)
    debt_history = db.query(CustomerDebt).filter(
        CustomerDebt.customer_id == customer.id
    ).order_by(desc(CustomerDebt.created_at)).limit(20).all()
    
    history_data = []
    for record in debt_history:
        # CustomerDebt transaction_type: "debt", "payment", "advance", "return"
        type_map = {
            "debt":     "🛒 Xarid qarzi",
            "payment":  "💰 To'lov",
            "advance":  "📥 Avans",
            "return":   "↩️ Qaytarish",
            # uppercase variантлар ҳам (эски маълумотлар учун)
            "DEBT":     "🛒 Xarid qarzi",
            "PAYMENT":  "💰 To'lov",
            "ADVANCE":  "📥 Avans",
            "RETURN":   "↩️ Qaytarish",
            "SALE":     "🛒 Xarid",
        }
        tx_type = record.transaction_type or ""
        history_data.append({
            "id": record.id,
            "transaction_type": tx_type,
            "type_text": type_map.get(tx_type, type_map.get(tx_type.upper(), tx_type)),
            "amount": float(record.amount or 0),
            "balance_after": float(record.balance_after or 0),
            "description": record.description or "",
            "date": record.created_at.isoformat() if record.created_at else None,
        })
    
    # Kompaniya ma'lumotlari DB dan
    company = get_company_info(db)

    return {
        "success": True,
        "data": {
            "current_debt": float(customer.current_debt or 0),
            "advance_balance": float(customer.advance_balance or 0),
            "debt_sales": debt_sales_data,
            "debt_sales_count": len(debt_sales_data),
            "history": history_data,
            "company_name": company["name"],
            "company_phone": company["phone"],
        }
    }


@router.post("/verify-webapp")
async def verify_webapp(
    data: VerifyWebAppRequest,
    db: Session = Depends(get_db)
):
    """
    Telegram WebApp initData ni tekshiradi.
    To'g'ri bo'lsa, mijoz ma'lumotlarini qaytaradi.
    Bu endpoint WebApp yuklanganda chaqiriladi.
    """
    bot_token = getattr(settings, "telegram_bot_token", None) or ""
    
    # Development rejimida tekshirishni o'tkazib yuborish
    if not bot_token or bot_token == "dev":
        # Test rejimi: init_data dan telegram_id ni parse qilish
        try:
            params = {}
            for item in data.init_data.split("&"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    params[k] = v
            user_data = json.loads(params.get("user", "{}"))
            telegram_id = str(user_data.get("id", ""))
        except Exception:
            raise HTTPException(status_code=400, detail="initData noto'g'ri formatda")
    else:
        # Production: to'liq tekshirish
        verified = verify_telegram_init_data(data.init_data, bot_token)
        if not verified:
            raise HTTPException(status_code=401, detail="initData noto'g'ri yoki eskirgan")
        user_data = verified.get("user_parsed", {})
        telegram_id = str(user_data.get("id", ""))
    
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Foydalanuvchi ID topilmadi")
    
    # Mijozni toping
    customer = get_customer_by_telegram_id(telegram_id, db)
    if not customer:
        return {
            "success": False,
            "registered": False,
            "telegram_id": telegram_id,
            "message": "Siz hali ro'yxatdan o'tmagansiz. Botga /start yuboring."
        }
    
    return {
        "success": True,
        "registered": True,
        "telegram_id": telegram_id,
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "current_debt": float(customer.current_debt or 0),
            "advance_balance": float(customer.advance_balance or 0),
            "total_purchases": float(customer.total_purchases or 0),
            "total_purchases_count": customer.total_purchases_count or 0,
            "customer_type": customer.customer_type.value if customer.customer_type else "regular",
        }
    }
