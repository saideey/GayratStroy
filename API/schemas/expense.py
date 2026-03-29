"""
Expense (Chiqimlar) schemas.
Request va response uchun Pydantic modellari.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────
# KATEGORIYA SCHEMAS
# ─────────────────────────────────────────────

class ExpenseCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = None

    class Config:
        str_strip_whitespace = True


class ExpenseCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        str_strip_whitespace = True


class ExpenseCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    is_active: bool
    created_at: datetime
    total_amount_uzs: Optional[Decimal] = None   # filter uchun hisoblangan

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# CHIQIM SCHEMAS
# ─────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(..., pattern=r'^(uzs|usd)$')
    usd_rate: Optional[Decimal] = Field(None, gt=0)   # USD bo'lsa majburiy
    expense_date: date
    category_id: int

    class Config:
        str_strip_whitespace = True

    @field_validator('usd_rate')
    @classmethod
    def validate_usd_rate(cls, v, info):
        if info.data.get('currency') == 'usd' and not v:
            raise ValueError("USD da yozilganda kurs (usd_rate) kiritilishi shart")
        return v


class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, pattern=r'^(uzs|usd)$')
    usd_rate: Optional[Decimal] = Field(None, gt=0)
    expense_date: Optional[date] = None
    category_id: Optional[int] = None
    comment: str = Field(..., min_length=3, max_length=500)  # MAJBURIY izoh

    class Config:
        str_strip_whitespace = True


class ExpenseDeleteRequest(BaseModel):
    comment: str = Field(..., min_length=3, max_length=500)  # MAJBURIY izoh


# ─────────────────────────────────────────────
# AUDIT LOG SCHEMA
# ─────────────────────────────────────────────

class ExpenseEditLogResponse(BaseModel):
    id: int
    action: str
    comment: str
    changed_at: datetime
    changed_by_id: int
    changed_by_name: str

    # Eski qiymatlar
    old_title: Optional[str]
    old_amount: Optional[Decimal]
    old_currency: Optional[str]
    old_category_id: Optional[int]
    old_expense_date: Optional[date]

    # Yangi qiymatlar
    new_title: Optional[str]
    new_amount: Optional[Decimal]
    new_currency: Optional[str]
    new_category_id: Optional[int]
    new_expense_date: Optional[date]

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# RESPONSE SCHEMAS
# ─────────────────────────────────────────────

class ExpenseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    amount: Decimal
    currency: str
    usd_rate: Optional[Decimal]
    amount_uzs: Optional[Decimal]
    expense_date: date
    category_id: int
    category_name: str
    category_color: Optional[str]
    created_by_id: int
    created_by_name: str
    is_deleted: bool
    deleted_at: Optional[datetime]
    deleted_by_id: Optional[int]
    deleted_by_name: Optional[str]
    delete_comment: Optional[str]
    created_at: datetime
    updated_at: datetime
    edit_logs: List[ExpenseEditLogResponse] = []

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    items: List[ExpenseResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    summary: "ExpenseSummary"


class ExpenseSummary(BaseModel):
    total_uzs: Decimal = Decimal('0')
    total_usd: Decimal = Decimal('0')
    total_uzs_equivalent: Decimal = Decimal('0')  # USD → UZS ga aylantirilgan jami
    by_category: List["CategorySummaryItem"] = []


class CategorySummaryItem(BaseModel):
    category_id: int
    category_name: str
    category_color: Optional[str]
    total_uzs: Decimal
    count: int


# ─────────────────────────────────────────────
# FILTER PARAMS
# ─────────────────────────────────────────────

class ExpenseFilterParams(BaseModel):
    category_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currency: Optional[str] = None
    include_deleted: bool = False
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
