"""
Suppliers router - Ta'minotchilar va hisob-kitoblar API.
MUHIM: Statik routerlar /{supplier_id} dan OLDIN joylashtirilgan.
"""

from typing import Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import io

from database import get_db
from database.models import User
from core.dependencies import get_current_active_user
from services.supplier import SupplierService

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    inn: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
    class Config:
        str_strip_whitespace = True

class SupplierUpdate(SupplierCreate):
    name: Optional[str] = Field(None, min_length=1, max_length=300)
    is_active: Optional[bool] = None

class TransactionCreate(BaseModel):
    transaction_type: str = Field(..., pattern='^(debt|payment|return)$')
    amount: Decimal = Field(..., gt=0)
    currency: str = Field('uzs', pattern='^(uzs|usd)$')
    usd_rate: Optional[Decimal] = Field(None, gt=0)
    transaction_date: date
    comment: str = Field(..., min_length=3, max_length=1000)
    purchase_order_id: Optional[int] = None
    class Config:
        str_strip_whitespace = True

class TransactionDeleteRequest(BaseModel):
    comment: str = Field(..., min_length=3, max_length=500)


# ═════════════════════════════════════════════════════════════════════════════
# STATIK ENDPOINTLAR — /{supplier_id} dan OLDIN bo'lishi SHART
# ═════════════════════════════════════════════════════════════════════════════

@router.get("", summary="Ta'minotchilar ro'yxati")
async def get_suppliers(
    q: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    has_debt: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SupplierService(db)
    suppliers, total, total_pages, total_debt = service.get_suppliers(
        q=q, is_active=is_active, has_debt=has_debt, page=page, per_page=per_page
    )
    return {
        "success": True,
        "data": {
            "items": [service.format_supplier(s) for s in suppliers],
            "total": total, "page": page, "per_page": per_page,
            "total_pages": total_pages, "total_debt": total_debt,
        }
    }


@router.post("", status_code=status.HTTP_201_CREATED, summary="Ta'minotchi yaratish")
async def create_supplier(
    data: SupplierCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SupplierService(db)
    try:
        supplier = service.create_supplier(data.model_dump(), current_user)
        return {"success": True, "data": service.format_supplier(supplier), "message": "Ta'minotchi yaratildi"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── STATIK: /export/excel — /{id} DAN OLDIN ──────────────────────────────────
@router.get("/export/excel", summary="Barcha ta'minotchilar Excel")
async def export_suppliers_excel(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    transaction_type: Optional[str] = Query(None, pattern="^(debt|payment|return)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from services.excel_export import generate_suppliers_excel
    data = generate_suppliers_excel(db=db, start_date=start_date, end_date=end_date,
                                     transaction_type=transaction_type)
    filename = f"taminotchilar_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ── STATIK: /transactions/{id} O'chirish ─────────────────────────────────────
@router.delete("/transactions/{transaction_id}", summary="Tranzaksiyani o'chirish (izoh majburiy)")
async def delete_transaction(
    transaction_id: int,
    data: TransactionDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SupplierService(db)
    try:
        service.delete_transaction(transaction_id, data.comment, current_user)
        return {"success": True, "message": "Tranzaksiya o'chirildi"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═════════════════════════════════════════════════════════════════════════════
# DINAMIK ENDPOINTLAR — /{supplier_id}
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/{supplier_id}", summary="Bitta ta'minotchi")
async def get_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SupplierService(db)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Ta'minotchi topilmadi")
    return {"success": True, "data": service.format_supplier(supplier)}


@router.put("/{supplier_id}", summary="Ta'minotchini yangilash")
async def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SupplierService(db)
    try:
        supplier = service.update_supplier(supplier_id, data.model_dump(exclude_none=True))
        return {"success": True, "data": service.format_supplier(supplier), "message": "Yangilandi"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{supplier_id}", summary="Ta'minotchini o'chirish")
async def delete_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SupplierService(db)
    try:
        service.delete_supplier(supplier_id, current_user)
        return {"success": True, "message": "Ta'minotchi o'chirildi"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{supplier_id}/stats", summary="Ta'minotchi to'liq statistikasi")
async def get_supplier_stats(
    supplier_id: int,
    start_date: Optional[date] = Query(None, description="Boshlanish sanasi"),
    end_date: Optional[date] = Query(None, description="Tugash sanasi"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SupplierService(db)
    try:
        stats = service.get_supplier_stats(
            supplier_id=supplier_id,
            start_date=start_date,
            end_date=end_date,
        )
        return {"success": True, "data": stats}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{supplier_id}/transactions", summary="Tranzaksiyalar ro'yxati")
async def get_transactions(
    supplier_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    transaction_type: Optional[str] = Query(None, pattern='^(debt|payment|return)$'),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    include_deleted: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SupplierService(db)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Ta'minotchi topilmadi")

    txs, total, total_pages, summary = service.get_transactions(
        supplier_id=supplier_id, include_deleted=include_deleted,
        transaction_type=transaction_type, start_date=start_date,
        end_date=end_date, page=page, per_page=per_page,
    )
    return {
        "success": True,
        "data": {
            "supplier": service.format_supplier(supplier),
            "items": txs, "total": total, "page": page,
            "per_page": per_page, "total_pages": total_pages, "summary": summary,
        }
    }


@router.post("/{supplier_id}/transactions", status_code=status.HTTP_201_CREATED,
             summary="Qarz yoki to'lov yozish (izoh majburiy)")
async def add_transaction(
    supplier_id: int,
    data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SupplierService(db)
    try:
        tx = service.add_transaction(
            supplier_id=supplier_id, transaction_type=data.transaction_type,
            amount=data.amount, currency=data.currency, comment=data.comment,
            current_user=current_user, transaction_date=data.transaction_date,
            usd_rate=data.usd_rate, purchase_order_id=data.purchase_order_id,
        )
        return {"success": True, "data": service._format_tx(tx), "message": "Tranzaksiya yozildi"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{supplier_id}/export/excel", summary="Bitta ta'minotchi Excel")
async def export_single_supplier_excel(
    supplier_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    transaction_type: Optional[str] = Query(None, pattern="^(debt|payment|return)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from services.excel_export import generate_suppliers_excel
    service = SupplierService(db)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Ta'minotchi topilmadi")
    data = generate_suppliers_excel(db=db, supplier_id=supplier_id,
                                     start_date=start_date, end_date=end_date,
                                     transaction_type=transaction_type)
    safe_name = "".join(c for c in supplier.name if c.isalnum() or c in " _-")[:30]
    filename = f"supplier_{safe_name}_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
