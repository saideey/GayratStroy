"""
Authentication router.
Handles login, logout, token refresh, password change.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.models import User
from core.dependencies import get_current_active_user
from schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    UserInfo,
    LogoutResponse,
)
from schemas.base import SuccessResponse, ErrorResponse
from services.auth import AuthService


router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "User blocked or inactive"},
    }
)
async def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with username and password.
    
    Returns access and refresh tokens along with user info.
    """
    auth_service = AuthService(db)
    
    user = auth_service.authenticate_user(data.username, data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username yoki parol noto'g'ri"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Foydalanuvchi faol emas"
        )
    
    if user.is_blocked:
        reason = user.blocked_reason or "Sabab ko'rsatilmagan"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Foydalanuvchi bloklangan: {reason}"
        )
    
    tokens = auth_service.create_tokens(user)
    user_info = auth_service.get_user_info(user)
    
    return LoginResponse(
        success=True,
        message="Muvaffaqiyatli kirdingiz",
        user=user_info,
        tokens=tokens
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
    }
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(db)
    
    tokens = auth_service.refresh_tokens(data.refresh_token)
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token yaroqsiz yoki muddati tugagan"
        )
    
    return tokens


@router.post(
    "/logout",
    response_model=LogoutResponse
)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user and invalidate all sessions.
    """
    auth_service = AuthService(db)
    auth_service.logout(current_user.id, "")
    
    return LogoutResponse()


@router.get(
    "/me",
    response_model=UserInfo
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user info.
    """
    auth_service = AuthService(db)
    return auth_service.get_user_info(current_user)


@router.post(
    "/change-password",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid current password"},
    }
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.
    """
    auth_service = AuthService(db)
    
    success, message = auth_service.change_password(
        current_user,
        data.current_password,
        data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return SuccessResponse(message=message)
