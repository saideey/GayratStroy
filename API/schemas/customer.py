"""
Customer schemas.
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, field_validator

from .base import BaseSchema, TimestampMixin


class CustomerBase(BaseSchema):
    """Base customer schema."""
    
    name: str
    company_name: Optional[str] = None
    phone: str
    phone_secondary: Optional[str] = None
    telegram_id: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    customer_type: str = "REGULAR"  # REGULAR, VIP, WHOLESALE, CONTRACTOR
    credit_limit: Decimal = Decimal("0")
    personal_discount_percent: Decimal = Decimal("0")
    inn: Optional[str] = None
    notes: Optional[str] = None
    sms_enabled: bool = True
    email_enabled: bool = False
    
    @field_validator("phone", "phone_secondary")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize phone number."""
        if v is None:
            return v
        cleaned = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not cleaned.startswith("+"):
            cleaned = "+998" + cleaned.lstrip("0")
        return cleaned


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    
    # VIP credentials (optional)
    login: Optional[str] = None
    password: Optional[str] = None
    manager_id: Optional[int] = None


class CustomerUpdate(BaseSchema):
    """Schema for updating a customer."""
    
    name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    telegram_id: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    customer_type: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    personal_discount_percent: Optional[Decimal] = None
    inn: Optional[str] = None
    notes: Optional[str] = None
    sms_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase, TimestampMixin):
    """Customer response schema."""
    
    id: int
    login: Optional[str] = None
    current_debt: Decimal
    advance_balance: Decimal
    total_purchases: Decimal
    total_purchases_count: int
    last_purchase_date: Optional[date] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    is_active: bool


class CustomerListItem(BaseSchema):
    """Simplified customer for lists."""
    
    id: int
    name: str
    company_name: Optional[str] = None
    phone: str
    phone_secondary: Optional[str] = None
    telegram_id: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    customer_type: str
    credit_limit: Decimal = Decimal("0")
    current_debt: Decimal
    advance_balance: Decimal
    total_purchases: Decimal
    is_active: bool
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None  # Kassir ismi
    
    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Customer list response."""
    
    success: bool = True
    data: List[CustomerListItem]
    total: int
    page: int
    per_page: int


class CustomerSearchParams(BaseModel):
    """Customer search parameters."""
    
    q: Optional[str] = None  # Search query (name, phone, company)
    customer_type: Optional[str] = None
    has_debt: Optional[bool] = None
    is_active: bool = True
    manager_id: Optional[int] = None
    sort_by: str = "name"
    sort_order: str = "asc"


class CustomerDebtResponse(BaseSchema):
    """Customer debt transaction response."""
    
    id: int
    customer_id: int
    transaction_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    created_by_id: int
    created_by_name: Optional[str] = None


class CustomerDebtListResponse(BaseModel):
    """Customer debt history response."""
    
    success: bool = True
    data: List[CustomerDebtResponse]
    total: int
    current_debt: Decimal
    advance_balance: Decimal


class CustomerPaymentRequest(BaseModel):
    """Customer payment (debt reduction) request."""
    
    amount: Decimal
    payment_type: str = "CASH"  # CASH, CARD, TRANSFER
    description: Optional[str] = None
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate payment amount."""
        if v <= 0:
            raise ValueError("To'lov summasi 0 dan katta bo'lishi kerak")
        return v


class CustomerAdvanceRequest(BaseModel):
    """Customer advance payment request."""
    
    amount: Decimal
    payment_type: str = "CASH"
    description: Optional[str] = None
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate advance amount."""
        if v <= 0:
            raise ValueError("Avans summasi 0 dan katta bo'lishi kerak")
        return v


class VIPLoginRequest(BaseModel):
    """VIP customer login request."""
    
    login: str
    password: str


class VIPCustomerResponse(BaseSchema):
    """VIP customer personal cabinet info."""
    
    id: int
    name: str
    company_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    current_debt: Decimal
    advance_balance: Decimal
    total_purchases: Decimal
    personal_discount_percent: Decimal


class VIPCredentialsCreate(BaseModel):
    """Create VIP credentials for customer."""
    
    login: str
    password: str
    
    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        """Validate login."""
        if len(v) < 3:
            raise ValueError("Login kamida 3 ta belgidan iborat bo'lishi kerak")
        return v.strip().lower()
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password."""
        if len(v) < 6:
            raise ValueError("Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        return v
