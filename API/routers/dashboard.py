"""
Dashboard API.
Endpoint: GET /api/v1/dashboard
"""

from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database import get_db
from database.models import User, Sale, SaleItem, Payment, Customer
from database.models.user import RoleType
from database.models.warehouse import Stock
from database.models.product import Product, UnitOfMeasure
from database.models.supplier import Supplier
from database.models.expense import Expense
from core.dependencies import get_current_active_user

router = APIRouter()


def _is_director(user: User) -> bool:
    """User direktor ekanligini to'g'ri tekshirish: user.role.role_type orqali."""
    try:
        return bool(user.role and user.role.role_type == RoleType.DIRECTOR)
    except Exception:
        return False


@router.get("", summary="Dashboard to'liq statistika")
async def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    yesterday = today - timedelta(days=1)
    month_start = today.replace(day=1)
    is_director = _is_director(current_user)

    DAYS_UZ = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]

    # ── Sotuv yordamchi funksiyasi ────────────────────────────────────────────
    def get_sales(from_date: date, to_date: date = None):
        q = db.query(Sale).filter(
            Sale.sale_date >= from_date,
            Sale.is_cancelled == False
        )
        if to_date:
            q = q.filter(Sale.sale_date <= to_date)
        else:
            q = q.filter(Sale.sale_date == from_date)
        if not is_director:
            q = q.filter(Sale.seller_id == current_user.id)
        return q.all()

    # ── 1. BUGUNGI SOTUVLAR ───────────────────────────────────────────────────
    today_sales = get_sales(today)
    today_revenue = sum(float(s.total_amount or 0) for s in today_sales)
    today_paid    = sum(float(s.paid_amount or 0) for s in today_sales)
    today_debt    = sum(float(s.debt_amount or 0) for s in today_sales)

    # Tannarxni SQL orqali hisoblash (lazy loading muammosini hal qiladi)
    today_cost_raw = db.query(
        func.coalesce(func.sum(SaleItem.unit_cost * SaleItem.base_quantity), 0)
    ).join(Sale, Sale.id == SaleItem.sale_id).filter(
        Sale.sale_date == today, Sale.is_cancelled == False
    )
    if not is_director:
        today_cost_raw = today_cost_raw.filter(Sale.seller_id == current_user.id)
    today_cost = Decimal(str(today_cost_raw.scalar() or 0))
    today_gross = float(Decimal(str(today_revenue)) - today_cost)

    # Bugungi chiqimlar
    today_expenses = 0.0
    if is_director:
        from sqlalchemy import case as sa_case
        res = db.query(func.coalesce(func.sum(
            sa_case((Expense.amount_uzs.isnot(None), Expense.amount_uzs), else_=Expense.amount)
        ), 0)).filter(
            Expense.is_deleted == False, Expense.expense_date == today
        ).scalar()
        today_expenses = float(res or 0)
    today_profit = today_gross - today_expenses

    # ── 2. KECHAGI SOTUV (o'zgarish % uchun) ─────────────────────────────────
    yesterday_sales = get_sales(yesterday)
    yesterday_revenue = sum(float(s.total_amount or 0) for s in yesterday_sales)
    change_pct = 0.0
    if yesterday_revenue > 0:
        change_pct = round((today_revenue - yesterday_revenue) / yesterday_revenue * 100, 1)

    # ── 3. TO'LOV USULLARI (bugun) ────────────────────────────────────────────
    pay_map: dict = {"cash": 0.0, "card": 0.0, "transfer": 0.0, "other": 0.0}
    if today_sales:
        s_ids = [s.id for s in today_sales]
        pay_rows = db.query(
            Payment.payment_type,
            func.coalesce(func.sum(Payment.amount), 0).label("total")
        ).filter(
            Payment.sale_id.in_(s_ids),
            Payment.is_cancelled == False
        ).group_by(Payment.payment_type).all()
        for row in pay_rows:
            k = row.payment_type.value if hasattr(row.payment_type, 'value') else str(row.payment_type)
            pay_map[k] = float(row.total or 0)

    # ── 4. OYLIK STATISTIKA ───────────────────────────────────────────────────
    month_sales = get_sales(month_start, today)
    month_revenue = sum(float(s.total_amount or 0) for s in month_sales)
    month_cost_raw = db.query(
        func.coalesce(func.sum(SaleItem.unit_cost * SaleItem.base_quantity), 0)
    ).join(Sale, Sale.id == SaleItem.sale_id).filter(
        Sale.sale_date >= month_start, Sale.sale_date <= today, Sale.is_cancelled == False
    )
    if not is_director:
        month_cost_raw = month_cost_raw.filter(Sale.seller_id == current_user.id)
    month_cost = Decimal(str(month_cost_raw.scalar() or 0))
    month_gross = float(Decimal(str(month_revenue)) - month_cost)

    month_expenses = 0.0
    if is_director:
        from sqlalchemy import case as sa_case
        res = db.query(func.coalesce(func.sum(
            sa_case((Expense.amount_uzs.isnot(None), Expense.amount_uzs), else_=Expense.amount)
        ), 0)).filter(
            Expense.is_deleted == False,
            Expense.expense_date >= month_start,
            Expense.expense_date <= today,
        ).scalar()
        month_expenses = float(res or 0)

    # ── 5. 7 KUNLIK GRAFIK ────────────────────────────────────────────────────
    daily_chart = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_sales = get_sales(d)
        rev = sum(float(s.total_amount or 0) for s in d_sales)
        daily_chart.append({
            "date": d.isoformat(),
            "day_name": DAYS_UZ[d.weekday()],
            "day": str(d.day),
            "revenue": rev,
            "count": len(d_sales),
        })

    # ── 6. BUGUNGI TOP MAHSULOTLAR (SQL query) ──────────────────────────────
    top_products = []
    if today_sales:
        s_ids_today = [s.id for s in today_sales]
        top_raw = db.query(
            Product.id,
            Product.name,
            func.coalesce(func.sum(SaleItem.quantity), 0).label("qty"),
            func.coalesce(func.sum(SaleItem.total_price), 0).label("revenue"),
        ).join(SaleItem, SaleItem.product_id == Product.id).filter(
            SaleItem.sale_id.in_(s_ids_today)
        ).group_by(Product.id, Product.name).order_by(
            func.sum(SaleItem.total_price).desc()
        ).limit(5).all()
        top_products = [
            {"name": r.name, "qty": float(r.qty or 0), "revenue": float(r.revenue or 0)}
            for r in top_raw
        ]

    # ── 7. SOTUVCHILAR REYTINGI (bu oy, faqat direktor) ──────────────────────
    seller_stats = []
    if is_director:
        seller_rows = db.query(
            Sale.seller_id,
            func.count(Sale.id).label("cnt"),
            func.coalesce(func.sum(Sale.total_amount), 0).label("amt"),
        ).filter(
            Sale.sale_date >= month_start, Sale.sale_date <= today,
            Sale.is_cancelled == False, Sale.seller_id.isnot(None)
        ).group_by(Sale.seller_id).order_by(func.sum(Sale.total_amount).desc()).limit(5).all()

        for row in seller_rows:
            u = db.query(User).filter(User.id == row.seller_id).first()
            if u:
                seller_stats.append({
                    "name": f"{u.first_name} {u.last_name}".strip(),
                    "count": row.cnt,
                    "revenue": float(row.amt or 0),
                })

    # ── 8. MIJOZ QARZDORLAR ───────────────────────────────────────────────────
    debtor_q = db.query(Customer).filter(
        Customer.is_deleted == False,
        Customer.current_debt > 0
    )
    if not is_director:
        debtor_q = debtor_q.filter(Customer.manager_id == current_user.id)

    debtors = debtor_q.order_by(Customer.current_debt.desc()).all()
    total_cust_debt = sum(float(c.current_debt or 0) for c in debtors)

    # ── 9. TA'MINOTCHI QARZLARI ───────────────────────────────────────────────
    sup_debtors, total_sup_debt = [], 0.0
    if is_director:
        sup_rows = db.query(Supplier).filter(
            Supplier.is_deleted == False,
            Supplier.current_debt > 0
        ).order_by(Supplier.current_debt.desc()).all()
        total_sup_debt = sum(float(s.current_debt or 0) for s in sup_rows)
        sup_debtors = [
            {"id": s.id, "name": s.name, "debt": float(s.current_debt or 0)}
            for s in sup_rows[:5]
        ]

    # ── 10. KAM QOLGAN TOVARLAR ───────────────────────────────────────────────
    # MUHIM: min_stock_level (min_stock emas), base_uom_id orqali UOM olamiz
    try:
        low_rows = db.query(
            Product.id,
            Product.name,
            Product.min_stock_level,
            Product.base_uom_id,
            func.coalesce(func.sum(Stock.quantity), 0).label("current_stock"),
        ).outerjoin(
            Stock, Stock.product_id == Product.id
        ).filter(
            Product.is_deleted == False,
            Product.is_active == True,
            Product.min_stock_level > 0,
        ).group_by(
            Product.id, Product.name, Product.min_stock_level, Product.base_uom_id
        ).having(
            func.coalesce(func.sum(Stock.quantity), 0) < Product.min_stock_level
        ).order_by(
            func.coalesce(func.sum(Stock.quantity), 0).asc()
        ).limit(8).all()

        # UOM symbollarini bitta so'rovda olamiz
        uom_ids = list({r.base_uom_id for r in low_rows if r.base_uom_id})
        uom_map = {}
        if uom_ids:
            for uom in db.query(UnitOfMeasure).filter(UnitOfMeasure.id.in_(uom_ids)).all():
                uom_map[uom.id] = uom.symbol

        low_stock_items = [{
            "product_id": r.id,
            "product_name": r.name,
            "current_stock": float(r.current_stock),
            "min_stock": float(r.min_stock_level),
            "uom": uom_map.get(r.base_uom_id, "dona"),
        } for r in low_rows]

    except Exception as e:
        low_stock_items = []

    # ── 11. OMBOR UMUMIY ──────────────────────────────────────────────────────
    try:
        wh_value = float(db.query(
            func.coalesce(func.sum(Stock.quantity * Stock.average_cost), 0)
        ).scalar() or 0)
        wh_products = db.query(func.count(Stock.id)).filter(
            Stock.quantity > 0
        ).scalar() or 0
    except Exception:
        wh_value, wh_products = 0.0, 0

    # ── JAVOB ─────────────────────────────────────────────────────────────────
    return {
        "success": True,
        "data": {
            "today": {
                "date": today.isoformat(),
                "sales_count": len(today_sales),
                "revenue": today_revenue,
                "paid": today_paid,
                "debt_added": today_debt,
                "expenses": today_expenses,
                "profit": today_profit,
                "yesterday_revenue": yesterday_revenue,
                "change_percent": change_pct,
                "payment_methods": pay_map,
            },
            "month": {
                "label": month_start.strftime("%B %Y"),
                "sales_count": len(month_sales),
                "revenue": month_revenue,
                "expenses": month_expenses,
                "profit": month_gross - month_expenses,
            },
            "daily_chart": daily_chart,
            "top_products": top_products,
            "seller_stats": seller_stats,
            "customers": {
                "total_debt": total_cust_debt,
                "debtors_count": len(debtors),
                "top_debtors": [{
                    "id": c.id, "name": c.name,
                    "phone": c.phone or "",
                    "debt": float(c.current_debt or 0),
                } for c in debtors[:8]],
            },
            "suppliers": {
                "total_debt": total_sup_debt,
                "debtors_count": len(sup_debtors),
                "top_debtors": sup_debtors,
            },
            "warehouse": {
                "total_value": wh_value,
                "total_products": wh_products,
                "low_stock_count": len(low_stock_items),
                "low_stock_items": low_stock_items,
            },
            "is_director": is_director,
        }
    }


@router.get("/summary", summary="Dashboard summary (alias)")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return await get_dashboard(current_user=current_user, db=db)
