"""
User management service.
"""

from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from database.models import User, Role, AuditLog
from core.security import get_password_hash
from schemas.user import UserCreate, UserUpdate, UserResponse
from utils.helpers import get_tashkent_now


class UserService:
    """User management service class."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(
            User.id == user_id,
            User.is_deleted == False
        ).first()
    
    def get_user_by_username(self, username: str, include_deleted: bool = False) -> Optional[User]:
        """Get user by username."""
        query = self.db.query(User).filter(
            User.username == username.lower().strip()
        )
        if not include_deleted:
            query = query.filter(User.is_deleted == False)
        return query.first()
    
    def username_exists(self, username: str) -> bool:
        """Check if username exists (including deleted users for unique constraint)."""
        return self.db.query(User).filter(
            User.username == username.lower().strip()
        ).first() is not None
    
    def get_users(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        warehouse_id: Optional[int] = None
    ) -> Tuple[List[User], int]:
        """
        Get paginated users list.
        
        Returns:
            Tuple of (users list, total count)
        """
        query = self.db.query(User).filter(User.is_deleted == False)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.phone.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        if role_id:
            query = query.filter(User.role_id == role_id)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if warehouse_id:
            query = query.filter(User.assigned_warehouse_id == warehouse_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.order_by(User.created_at.desc()).offset(offset).limit(per_page).all()
        
        return users, total
    
    def create_user(self, data: UserCreate, created_by_id: int) -> Tuple[User, str]:
        """
        Create new user.
        
        Args:
            data: User creation data
            created_by_id: ID of user creating this user
            
        Returns:
            Tuple of (created user, message)
        """
        # Check username uniqueness (including deleted users for unique constraint)
        if self.username_exists(data.username):
            return None, "Bu username allaqachon mavjud"
        
        # Check email uniqueness (including deleted users)
        if data.email:
            email_exists = self.db.query(User).filter(
                User.email == data.email
            ).first()
            if email_exists:
                return None, "Bu email allaqachon mavjud"
        
        # Check role exists
        role = self.db.query(Role).filter(Role.id == data.role_id).first()
        if not role:
            return None, "Rol topilmadi"
        
        try:
            # Create user
            user = User(
                username=data.username.lower().strip(),
                email=data.email,
                password_hash=get_password_hash(data.password),
                first_name=data.first_name,
                last_name=data.last_name,
                phone=data.phone,
                role_id=data.role_id,
                assigned_warehouse_id=data.assigned_warehouse_id,
                is_active=True,
                is_blocked=False
            )
            
            self.db.add(user)
            self.db.flush()  # Get user ID
            
            # Log action
            self._log_action(created_by_id, "create", "users", user.id, f"Foydalanuvchi yaratildi: {user.username}")
            
            self.db.commit()
            self.db.refresh(user)
            
            return user, "Foydalanuvchi muvaffaqiyatli yaratildi"
        except IntegrityError as e:
            self.db.rollback()
            error_str = str(e).lower()
            if "username" in error_str:
                return None, "Bu username allaqachon mavjud"
            elif "email" in error_str:
                return None, "Bu email allaqachon mavjud"
            else:
                return None, "Ma'lumotlar bazasida xatolik: takroriy ma'lumot"
        except Exception as e:
            self.db.rollback()
            return None, f"Xatolik yuz berdi: {str(e)}"
    
    def update_user(
        self,
        user_id: int,
        data: UserUpdate,
        updated_by_id: int
    ) -> Tuple[Optional[User], str]:
        """
        Update user.
        
        Args:
            user_id: User ID to update
            data: Update data
            updated_by_id: ID of user making the update
            
        Returns:
            Tuple of (updated user or None, message)
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None, "Foydalanuvchi topilmadi"
        
        # Store old values for audit
        old_values = {}
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                old_values[field] = getattr(user, field)
                setattr(user, field, value)
        
        # Log action
        self._log_action(
            updated_by_id, "update", "users", user.id,
            f"Foydalanuvchi yangilandi: {user.username}",
            old_values=old_values,
            new_values=update_data
        )
        
        self.db.commit()
        self.db.refresh(user)
        
        return user, "Foydalanuvchi muvaffaqiyatli yangilandi"
    
    def delete_user(self, user_id: int, deleted_by_id: int) -> Tuple[bool, str]:
        """
        Soft delete user.
        
        Args:
            user_id: User ID to delete
            deleted_by_id: ID of user performing deletion
            
        Returns:
            Tuple of (success, message)
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "Foydalanuvchi topilmadi"
        
        if user.id == deleted_by_id:
            return False, "O'zingizni o'chira olmaysiz"
        
        user.is_deleted = True
        user.deleted_at = get_tashkent_now()
        user.is_active = False
        
        # Log action
        self._log_action(deleted_by_id, "delete", "users", user.id, f"Foydalanuvchi o'chirildi: {user.username}")
        
        self.db.commit()
        
        return True, "Foydalanuvchi o'chirildi"
    
    def block_user(
        self,
        user_id: int,
        blocked_by_id: int,
        reason: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Block user."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "Foydalanuvchi topilmadi"
        
        if user.id == blocked_by_id:
            return False, "O'zingizni bloklash mumkin emas"
        
        user.is_blocked = True
        user.blocked_reason = reason
        
        self._log_action(blocked_by_id, "block", "users", user.id, f"Bloklandi: {reason}")
        
        self.db.commit()
        
        return True, "Foydalanuvchi bloklandi"
    
    def unblock_user(self, user_id: int, unblocked_by_id: int) -> Tuple[bool, str]:
        """Unblock user."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "Foydalanuvchi topilmadi"
        
        user.is_blocked = False
        user.blocked_reason = None
        
        self._log_action(unblocked_by_id, "unblock", "users", user.id, "Blokdan chiqarildi")
        
        self.db.commit()
        
        return True, "Foydalanuvchi blokdan chiqarildi"
    
    def reset_password(
        self,
        user_id: int,
        new_password: str,
        reset_by_id: int
    ) -> Tuple[bool, str]:
        """Reset user password (admin function)."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "Foydalanuvchi topilmadi"
        
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = get_tashkent_now().isoformat()
        user.failed_login_attempts = 0
        
        self._log_action(reset_by_id, "password_reset", "users", user.id, "Admin tomonidan parol tiklandi")
        
        self.db.commit()
        
        return True, "Parol tiklandi"
    
    def _log_action(
        self,
        user_id: int,
        action: str,
        table_name: str,
        record_id: int,
        description: str = None,
        old_values: dict = None,
        new_values: dict = None
    ) -> None:
        """Log user action for audit."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            description=description,
            old_values=old_values,
            new_values=new_values
        )
        self.db.add(log)


class RoleService:
    """Role management service class."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_roles(self, include_inactive: bool = False) -> List[Role]:
        """Get all roles."""
        query = self.db.query(Role).filter(Role.is_deleted == False)
        
        if not include_inactive:
            query = query.filter(Role.is_active == True)
        
        return query.order_by(Role.id).all()
    
    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        return self.db.query(Role).filter(
            Role.id == role_id,
            Role.is_deleted == False
        ).first()
    
    def create_role(self, data: dict, created_by_id: int) -> Tuple[Optional[Role], str]:
        """Create new role."""
        # Check name uniqueness
        existing = self.db.query(Role).filter(Role.name == data["name"]).first()
        if existing:
            return None, "Bu nom bilan rol mavjud"
        
        role = Role(**data, is_system=False)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        
        return role, "Rol yaratildi"
    
    def update_role(self, role_id: int, data: dict, updated_by_id: int) -> Tuple[Optional[Role], str]:
        """Update role."""
        role = self.get_role_by_id(role_id)
        if not role:
            return None, "Rol topilmadi"
        
        if role.is_system:
            return None, "Tizim rollarini o'zgartirish mumkin emas"
        
        for field, value in data.items():
            if hasattr(role, field) and value is not None:
                setattr(role, field, value)
        
        self.db.commit()
        self.db.refresh(role)
        
        return role, "Rol yangilandi"
    
    def delete_role(self, role_id: int, deleted_by_id: int) -> Tuple[bool, str]:
        """Delete role."""
        role = self.get_role_by_id(role_id)
        if not role:
            return False, "Rol topilmadi"
        
        if role.is_system:
            return False, "Tizim rollarini o'chirish mumkin emas"
        
        # Check if role has users
        users_count = self.db.query(User).filter(
            User.role_id == role_id,
            User.is_deleted == False
        ).count()
        
        if users_count > 0:
            return False, f"Bu rolga {users_count} ta foydalanuvchi biriktirilgan"
        
        role.is_deleted = True
        role.deleted_at = get_tashkent_now()
        
        self.db.commit()
        
        return True, "Rol o'chirildi"
