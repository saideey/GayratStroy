"""
Authentication service.
Handles login, logout, token management.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from database.models import User, UserSession, AuditLog
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    TokenData,
)
from core.config import settings
from schemas.auth import LoginRequest, TokenResponse, UserInfo
from utils.helpers import get_tashkent_now


class AuthService:
    """Authentication service class."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = self.db.query(User).filter(
            User.username == username.lower().strip(),
            User.is_deleted == False
        ).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            self.db.commit()
            return None
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = get_tashkent_now().isoformat()
        self.db.commit()
        
        return user
    
    def create_tokens(self, user: User) -> TokenResponse:
        """
        Create access and refresh tokens for user.
        
        Args:
            user: Authenticated user
            
        Returns:
            TokenResponse with both tokens
        """
        token_data = TokenData(
            user_id=user.id,
            username=user.username,
            role_id=user.role_id,
            role_type=user.role.role_type.value if user.role.role_type else "unknown"
        )
        
        access_token = create_access_token(token_data.to_dict())
        refresh_token = create_refresh_token(token_data.to_dict())
        
        # Store session
        self._create_session(user.id, refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    def refresh_tokens(self, refresh_token: str) -> Optional[TokenResponse]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New TokenResponse or None if invalid
        """
        payload = verify_refresh_token(refresh_token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = self.db.query(User).filter(
            User.id == int(user_id),
            User.is_active == True,
            User.is_deleted == False
        ).first()
        
        if not user:
            return None
        
        # Invalidate old session
        self._invalidate_session(refresh_token)
        
        # Create new tokens
        return self.create_tokens(user)
    
    def logout(self, user_id: int, token: str) -> bool:
        """
        Logout user and invalidate session.
        
        Args:
            user_id: User ID
            token: Current token
            
        Returns:
            True if successful
        """
        # Invalidate all sessions for user
        self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).update({"is_active": False})
        
        self.db.commit()
        return True
    
    def get_user_info(self, user: User) -> UserInfo:
        """
        Get user info for response.
        
        Args:
            user: User model instance
            
        Returns:
            UserInfo schema
        """
        return UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            role_id=user.role_id,
            role_name=user.role.display_name,
            role_type=user.role.role_type.value if user.role.role_type else "unknown",
            permissions=user.role.permissions or [],
            max_discount_percent=user.role.max_discount_percent,
            assigned_warehouse_id=user.assigned_warehouse_id,
            assigned_warehouse_name=user.assigned_warehouse.name if user.assigned_warehouse else None
        )
    
    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """
        Change user password.
        
        Args:
            user: Current user
            current_password: Current password
            new_password: New password
            
        Returns:
            Tuple of (success, message)
        """
        if not verify_password(current_password, user.password_hash):
            return False, "Joriy parol noto'g'ri"
        
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = get_tashkent_now().isoformat()
        
        # Log password change
        self._log_action(user.id, "password_change", "users", user.id)
        
        self.db.commit()
        return True, "Parol muvaffaqiyatli o'zgartirildi"
    
    def _create_session(self, user_id: int, token: str) -> UserSession:
        """Create user session record."""
        session = UserSession(
            user_id=user_id,
            token_hash=token[:50],  # Store partial hash for reference
            expires_at=(get_tashkent_now() + timedelta(days=settings.refresh_token_expire_days)).isoformat(),
            is_active=True
        )
        self.db.add(session)
        self.db.commit()
        return session
    
    def _invalidate_session(self, token: str) -> None:
        """Invalidate session by token."""
        self.db.query(UserSession).filter(
            UserSession.token_hash == token[:50]
        ).update({"is_active": False})
        self.db.commit()
    
    def _log_action(
        self,
        user_id: int,
        action: str,
        table_name: str,
        record_id: int,
        description: str = None
    ) -> None:
        """Log user action for audit."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            description=description
        )
        self.db.add(log)
