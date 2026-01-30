"""
Database package for G'ayrat Stroy House ERP.

Usage:
    from database import db, get_db, init_db
    from database.models import User, Product, Sale
"""

from .base import Base, BaseModel, TimestampMixin, SoftDeleteMixin
from .connection import (
    DatabaseConnection,
    db,
    get_db,
    init_db,
    reset_db,
)

# Import all models to ensure they are registered
from .models import *


__all__ = [
    # Base
    'Base',
    'BaseModel',
    'TimestampMixin',
    'SoftDeleteMixin',
    
    # Connection
    'DatabaseConnection',
    'db',
    'get_db',
    'init_db',
    'reset_db',
]
