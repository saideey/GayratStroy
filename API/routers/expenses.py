"""
Expenses router - Chiqimlar va kategoriyalar API.

Endpoints:
  Kategoriyalar:
    GET    /categories            - Ro'yxat
    POST   /categories            - Yaratish
    PUT    /categories/{id}       - Yangilash
    DELETE /categories/{id}       - O'chirish

  Chiqimlar:
    GET    /                      - Ro'yxat + filter
    POST   /                      - Yaratish
    GET    /{id}                  - Bitta + tarixi
    PUT    /{id}                  - Yangilash (izoh majburiy)
    DELETE /{id}                  - O'chirish (izoh majburiy)
    POST   /{id}/restore          - Tiklash
    GET    /{id}/logs             - O'zgartirish tarixi

  Hisobot:
    GET    /profit-summary        - Sof foyda hisobi
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from database.models import User
from core.dependencies import get_current_active_user
from services.expense import ExpenseService
from schemas.expense import (
    ExpenseCategoryCreate, ExpenseCategoryUpdate,
    ExpenseCreate, ExpenseUpdate, ExpenseDeleteRequest,
)

router = APIRouter()


# ══════════════════════════════════════════════
# KATEGORIYALAR
# ══════════════════════════════════════════════

@router.get("/categories", summary="Chiqim kategoriyalari ro'yxati")
async def get_categories(
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    categories = service.get_categories(include_inactive=include_inactive)
    return {"success": True, "data": categories}


@router.post("/categories", status_code=status.HTTP_201_CREATED, summary="Kategoriya yaratish")
async def create_category(
    data: ExpenseCategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    try:
        category = service.create_category(data)
        return {"success": True, "data": service._format_category(category), "message": "Kategoriya yaratildi"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/categories/{category_id}", summary="Kategoriyani yangilash")
async def update_category(
    category_id: int,
    data: ExpenseCategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    try:
        category = service.update_category(category_id, data)
        return {"success": True, "data": service._format_category(category), "message": "Kategoriya yangilandi"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/categories/{category_id}", summary="Kategoriyani o'chirish")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    try:
        service.delete_category(category_id)
        return {"success": True, "message": "Kategoriya deaktiv qilindi"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ══════════════════════════════════════════════
# CHIQIMLAR
# ══════════════════════════════════════════════

@router.get("", summary="Chiqimlar ro'yxati (filter bilan)")
async def get_expenses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None, description="Kategoriya bo'yicha filter"),
    start_date: Optional[date] = Query(None, description="Boshlanish sanasi"),
    end_date: Optional[date] = Query(None, description="Tugash sanasi"),
    currency: Optional[str] = Query(None, pattern="^(uzs|usd)$"),
    include_deleted: bool = Query(False, description="O'chirilganlarni ham ko'rsatish"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    items, total, total_pages, summary = service.get_expenses(
        page=page,
        per_page=per_page,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
        include_deleted=include_deleted,
    )
    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "summary": summary,
        }
    }


@router.post("", status_code=status.HTTP_201_CREATED, summary="Chiqim yozish")
async def create_expense(
    data: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    try:
        expense = service.create_expense(data, current_user)
        return {"success": True, "data": expense, "message": "Chiqim yozildi"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/profit-summary", summary="Sof foyda hisobi")
async def get_profit_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Sof foyda = Sotuv daromadi − Jami chiqimlar (UZS da)
    Dashboard va hisobotlar uchun ishlatiladi.
    """
    service = ExpenseService(db)
    summary = service.get_profit_summary(start_date=start_date, end_date=end_date)
    return {"success": True, "data": summary}


@router.get("/{expense_id}", summary="Bitta chiqim (tarixi bilan)")
async def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    expense = service.get_expense(expense_id)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chiqim topilmadi")
    return {"success": True, "data": expense}


@router.put("/{expense_id}", summary="Chiqimni yangilash (izoh majburiy)")
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    try:
        expense = service.update_expense(expense_id, data, current_user)
        return {"success": True, "data": expense, "message": "Chiqim yangilandi"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{expense_id}", summary="Chiqimni o'chirish (izoh majburiy)")
async def delete_expense(
    expense_id: int,
    data: ExpenseDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    try:
        result = service.delete_expense(expense_id, data.comment, current_user)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{expense_id}/restore", summary="O'chirilgan chiqimni tiklash")
async def restore_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    try:
        expense = service.restore_expense(expense_id, current_user)
        return {"success": True, "data": expense, "message": "Chiqim tiklandi"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{expense_id}/logs", summary="Chiqim o'zgartirish tarixi")
async def get_expense_logs(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    expense = service.get_expense(expense_id)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chiqim topilmadi")
    logs = service.get_expense_logs(expense_id)
    return {"success": True, "data": logs}


# ── Excel export ──────────────────────────────────────────────────────────────

from fastapi.responses import StreamingResponse
import io

@router.get("/export/excel", summary="Chiqimlar Excel export")
async def export_expenses_excel(
    category_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    currency: Optional[str] = Query(None, pattern="^(uzs|usd)$"),
    include_deleted: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from services.excel_export import generate_expenses_excel
    data = generate_expenses_excel(
        db=db,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
        include_deleted=include_deleted,
    )
    filename = f"chiqimlar_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
