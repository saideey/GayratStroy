"""
User and Role schemas.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator

from .base import BaseSchema, TimestampMixin


# ==================== ROLE SCHEMAS ====================

class RoleBase(BaseSchema):
    """Base role schema."""
    
    name: str
    display_name: str
    description: Optional[str] = None
    permissions: List[str] = []
    max_discount_percent: int = 0


class RoleCreate(RoleBase):
    """Schema for creating a role."""
    pass


class RoleUpdate(BaseSchema):
    """Schema for updating a role."""
    
    display_name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    max_discount_percent: Optional[int] = None
    is_active: Optional[bool] = None


class RoleResponse(RoleBase, TimestampMixin):
    """Role response schema."""
    
    id: int
    role_type: Optional[str] = None
    is_system: bool
    is_active: bool


class RoleListResponse(BaseModel):
    """Role list response."""
    
    success: bool = True
    data: List[RoleResponse]
    count: int


# ==================== USER SCHEMAS ====================

class UserBase(BaseSchema):
    """Base user schema."""
    
    username: str
    email: Optional[EmailStr] = None
    first_name: str
    last_name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    password: str
    role_id: int
    assigned_warehouse_id: Optional[int] = None
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username."""
        if len(v) < 3:
            raise ValueError("Username kamida 3 ta belgidan iborat bo'lishi kerak")
        if not v.replace("_", "").replace(".", "").isalnum():
            raise ValueError("Username faqat harf, raqam, _ va . dan iborat bo'lishi kerak")
        return v.strip().lower()
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 6:
            raise ValueError("Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number."""
        if v is None:
            return v
        # Remove spaces and dashes
        cleaned = v.replace(" ", "").replace("-", "")
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role_id: Optional[int] = None
    assigned_warehouse_id: Optional[int] = None
    is_active: Optional[bool] = None
    language: Optional[str] = None  # uz, ru, uz_cyrl


class UserLanguageUpdate(BaseSchema):
    """Schema for updating user's language preference."""
    
    language: str  # uz, ru, uz_cyrl
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        valid_languages = ['uz', 'ru', 'uz_cyrl']
        if v not in valid_languages:
            raise ValueError(f"Til kodi noto'g'ri. Mavjud tillar: {', '.join(valid_languages)}")
        return v


class UserResponse(UserBase, TimestampMixin):
    """User response schema."""
    
    id: int
    avatar_url: Optional[str] = None
    role_id: int
    role: Optional[RoleResponse] = None
    is_active: bool
    is_blocked: bool
    blocked_reason: Optional[str] = None
    assigned_warehouse_id: Optional[int] = None
    last_login: Optional[str] = None
    language: str = 'uz'  # User's language preference
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"


class UserListResponse(BaseModel):
    """User list response."""
    
    success: bool = True
    data: List[UserResponse]
    total: int
    page: int
    per_page: int


class UserBlockRequest(BaseModel):
    """Request to block a user."""
    
    reason: Optional[str] = None


class UserPasswordReset(BaseModel):
    """Admin password reset for user."""
    
    new_password: str
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 6:
            raise ValueError("Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        return v
