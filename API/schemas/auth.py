"""
Authentication schemas - login, token, registration.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re

from .base import BaseSchema


class LoginRequest(BaseModel):
    """Login request schema."""
    
    username: str
    password: str
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username."""
        if len(v) < 3:
            raise ValueError("Username kamida 3 ta belgidan iborat bo'lishi kerak")
        return v.strip().lower()


class TokenResponse(BaseModel):
    """Token response after successful login."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    
    current_password: str
    new_password: str
    confirm_password: str
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 6:
            raise ValueError("Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        return v
    
    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Parollar mos kelmaydi")
        return v


class UserInfo(BaseSchema):
    """Current user info response."""
    
    id: int
    username: str
    email: Optional[str] = None
    first_name: str
    last_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role_id: int
    role_name: str
    role_type: str
    permissions: list
    max_discount_percent: int
    assigned_warehouse_id: Optional[int] = None
    assigned_warehouse_name: Optional[str] = None


class LoginResponse(BaseModel):
    """Full login response with user info and tokens."""
    
    success: bool = True
    message: str = "Muvaffaqiyatli kirdingiz"
    user: UserInfo
    tokens: TokenResponse


class LogoutResponse(BaseModel):
    """Logout response."""
    
    success: bool = True
    message: str = "Muvaffaqiyatli chiqdingiz"
