"""
Base model class and common mixins for all database models.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()

# Tashkent timezone (UTC+5)
TASHKENT_TZ = timezone(timedelta(hours=5))

def get_tashkent_now():
    """Get current time in Tashkent timezone (as naive datetime)."""
    return datetime.now(TASHKENT_TZ).replace(tzinfo=None)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=get_tashkent_now, nullable=False)
    updated_at = Column(DateTime, default=get_tashkent_now, onupdate=get_tashkent_now, nullable=False)


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class BaseModel(Base, TimestampMixin):
    """Abstract base model with common fields."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        name = cls.__name__
        return ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_') + 's'
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
