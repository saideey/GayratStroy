"""
Users router.
Handles user management (CRUD, block/unblock, password reset).
Only accessible by Director role.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from database.models import User, RoleType
from core.dependencies import get_current_active_user, get_director_user
from core.security import verify_password, get_password_hash
from schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserBlockRequest,
    UserPasswordReset,
    UserLanguageUpdate,
    RoleResponse,
    RoleListResponse,
)
from schemas.base import SuccessResponse, ErrorResponse, DeleteResponse
from services.user import UserService, RoleService


router = APIRouter()


class ChangePasswordRequest(BaseModel):
    """Request to change own password."""
    current_password: str
    new_password: str


# ==================== CHANGE OWN PASSWORD ====================

@router.post(
    "/change-password",
    response_model=SuccessResponse,
    summary="O'z parolini o'zgartirish"
)
async def change_own_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change own password.
    
    Requires current password for verification.
    """
    # Verify current password
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Joriy parol noto'g'ri"
        )
    
    # Validate new password
    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yangi parol kamida 6 ta belgidan iborat bo'lishi kerak"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    
    return SuccessResponse(message="Parol muvaffaqiyatli o'zgartirildi")


# ==================== CHANGE LANGUAGE ====================

@router.put(
    "/language",
    response_model=SuccessResponse,
    summary="Tilni o'zgartirish"
)
async def change_language(
    data: UserLanguageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user's language preference.
    
    Available languages:
    - uz: O'zbek (lotin)
    - ru: Русский
    - uz_cyrl: Ўзбек (кирилл)
    """
    current_user.language = data.language
    db.commit()
    
    return SuccessResponse(message="Til muvaffaqiyatli o'zgartirildi")


# ==================== ROLES ====================

@router.get(
    "/roles",
    response_model=RoleListResponse,
    summary="Barcha rollarni olish"
)
async def get_roles(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all roles.
    
    - **include_inactive**: Include inactive roles
    """
    role_service = RoleService(db)
    roles = role_service.get_all_roles(include_inactive)
    
    return RoleListResponse(
        data=[RoleResponse.model_validate(r) for r in roles],
        count=len(roles)
    )


@router.get(
    "/roles/{role_id}",
    response_model=RoleResponse,
    summary="Rolni ID bo'yicha olish"
)
async def get_role(
    role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get role by ID."""
    role_service = RoleService(db)
    role = role_service.get_role_by_id(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol topilmadi"
        )
    
    return RoleResponse.model_validate(role)


# ==================== USERS ====================

@router.get(
    "",
    response_model=UserListResponse,
    summary="Foydalanuvchilar ro'yxati"
)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    warehouse_id: Optional[int] = None,
    current_user: User = Depends(get_director_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of users.
    
    Only accessible by Director.
    
    - **search**: Search by username, name, phone, email
    - **role_id**: Filter by role
    - **is_active**: Filter by active status
    - **warehouse_id**: Filter by assigned warehouse
    """
    user_service = UserService(db)
    users, total = user_service.get_users(
        page=page,
        per_page=per_page,
        search=search,
        role_id=role_id,
        is_active=is_active,
        warehouse_id=warehouse_id
    )
    
    return UserListResponse(
        data=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Foydalanuvchini ID bo'yicha olish"
)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_director_user),
    db: Session = Depends(get_db)
):
    """Get user by ID. Only accessible by Director."""
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )
    
    return UserResponse.model_validate(user)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi foydalanuvchi yaratish"
)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(get_director_user),
    db: Session = Depends(get_db)
):
    """
    Create new user.
    
    Only accessible by Director.
    """
    user_service = UserService(db)
    user, message = user_service.create_user(data, current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Foydalanuvchini yangilash"
)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(get_director_user),
    db: Session = Depends(get_db)
):
    """
    Update user.
    
    Only accessible by Director.
    """
    user_service = UserService(db)
    user, message = user_service.update_user(user_id, data, current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Foydalanuvchini yangilash (PUT)"
)
async def update_user_put(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(get_director_user),
    db: Session = Depends(get_db)
):
    """
    Update user (PUT method).
    
    Only accessible by Director.
    """
    user_service = UserService(db)
    user, message = user_service.update_user(user_id, data, current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/toggle-status",
    response_model=UserResponse,
    summary="Foydalanuvchi statusini o'zgartirish"
)
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(get_director_user),
    db: Session = Depends(get_db)
):
    """
    Toggle user active status.
    
    Only accessible by Director.
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O'zingizni bloklay olmaysiz"
        )
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    response_model=DeleteResponse,
    summary="Foydalanuvchini o'chirish"
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_director_user),
    db: Session = Depends(get_db)
):
    """
    Delete user (soft delete).
    
    Only accessible by Director.
    """
    user_service = UserService(db)
    success, message = user_service.delete_user(user_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return DeleteResponse(message=message, id=user_id)


@router.post(
    "/{user_id}/block",
    response_model=SuccessResponse,
    summary="Foydalanuvchini bloklash"
)
async def block_user(
    user_id: int,
    data: UserBlockRequest,
    current_user: User = Depends(get_director_user),
    db: Session = Depends(get_db)
):
    """
    Block user.
    
    Only accessible by Director.
    """
    user_service = UserService(db)
    success, message = user_service.block_user(user_id, current_user.id, data.reason)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return SuccessResponse(message=message)


@router.post(
    "/{user_id}/unblock",
    response_model=SuccessResponse,
    summary="Foydalanuvchini blokdan chiqarish"
)
async def unblock_user(
    user_id: int,
    current_user: User = Depends(get_director_user),
    db: Session = Depends(get_db)
):
    """
    Unblock user.
    
    Only accessible by Director.
    """
    user_service = UserService(db)
    success, message = user_service.unblock_user(user_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return SuccessResponse(message=message)


@router.post(
    "/{user_id}/reset-password",
    response_model=SuccessResponse,
    summary="Foydalanuvchi parolini tiklash"
)
async def reset_user_password(
    user_id: int,
    data: UserPasswordReset,
    current_user: User = Depends(get_director_user),
    db: Session = Depends(get_db)
):
    """
    Reset user password (admin function).
    
    Only accessible by Director.
    """
    user_service = UserService(db)
    success, message = user_service.reset_password(user_id, data.new_password, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return SuccessResponse(message=message)
