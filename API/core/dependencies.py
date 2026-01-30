"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from database.models import User, Role, PermissionType, RoleType
from .security import verify_access_token, TokenData


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token yaroqsiz yoki muddati tugagan",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active (non-blocked) user.
    
    Raises:
        HTTPException: If user is inactive or blocked
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Foydalanuvchi faol emas"
        )
    
    if current_user.is_blocked:
        reason = current_user.blocked_reason or "Sabab ko'rsatilmagan"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Foydalanuvchi bloklangan: {reason}"
        )
    
    if current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Foydalanuvchi o'chirilgan"
        )
    
    return current_user


class PermissionChecker:
    """
    Permission checker dependency.
    
    Usage:
        @router.get("/products", dependencies=[Depends(PermissionChecker([PermissionType.PRODUCT_VIEW]))])
        async def get_products():
            ...
    """
    
    def __init__(self, required_permissions: List[PermissionType]):
        self.required_permissions = required_permissions
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Check if user has required permissions."""
        
        # Director has all permissions
        if current_user.role.role_type == RoleType.DIRECTOR:
            return current_user
        
        # Check each required permission
        for permission in self.required_permissions:
            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Ruxsat yo'q: {permission.value}"
                )
        
        return current_user


class RoleChecker:
    """
    Role checker dependency.
    
    Usage:
        @router.delete("/users/{id}", dependencies=[Depends(RoleChecker([RoleType.DIRECTOR]))])
        async def delete_user():
            ...
    """
    
    def __init__(self, allowed_roles: List[RoleType]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Check if user has required role."""
        
        if current_user.role.role_type not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu amalni bajarish uchun ruxsatingiz yo'q"
            )
        
        return current_user


# Convenience dependencies for common role checks
async def get_director_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require director role."""
    if current_user.role.role_type != RoleType.DIRECTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat direktor uchun ruxsat berilgan"
        )
    return current_user


async def get_seller_or_above(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require seller role or above (director)."""
    allowed = [RoleType.DIRECTOR, RoleType.SELLER]
    if current_user.role.role_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat sotuvchi yoki direktor uchun"
        )
    return current_user


async def get_warehouse_manager_or_above(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require warehouse manager role or above."""
    allowed = [RoleType.DIRECTOR, RoleType.WAREHOUSE_MANAGER]
    if current_user.role.role_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat omborchi yoki direktor uchun"
        )
    return current_user


# Optional authentication (for endpoints that work with or without auth)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    user = db.query(User).filter(
        User.id == int(user_id),
        User.is_active == True,
        User.is_deleted == False
    ).first()
    
    return user
