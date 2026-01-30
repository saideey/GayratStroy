"""
Base schemas and common response models.
"""

from typing import TypeVar, Generic, Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    
    created_at: datetime
    updated_at: datetime


class SuccessResponse(BaseModel):
    """Standard success response."""
    
    success: bool = True
    message: str = "Muvaffaqiyatli bajarildi"


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    success: bool = False
    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    success: bool = True
    data: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    
    @classmethod
    def create(
        cls,
        data: List[T],
        total: int,
        page: int,
        per_page: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response."""
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return cls(
            data=data,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )


class DataResponse(BaseModel, Generic[T]):
    """Single data response wrapper."""
    
    success: bool = True
    data: T
    message: Optional[str] = None


class ListResponse(BaseModel, Generic[T]):
    """List data response wrapper."""
    
    success: bool = True
    data: List[T]
    count: int


class DeleteResponse(BaseModel):
    """Delete operation response."""
    
    success: bool = True
    message: str = "Muvaffaqiyatli o'chirildi"
    id: int


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    
    page: int = 1
    per_page: int = 20
    
    @property
    def offset(self) -> int:
        """Calculate offset for SQL query."""
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        """Get limit for SQL query."""
        return self.per_page


class SearchParams(BaseModel):
    """Search query parameters."""
    
    q: Optional[str] = None  # Search query
    sort_by: Optional[str] = None
    sort_order: str = "asc"  # asc or desc
    
    @property
    def is_descending(self) -> bool:
        """Check if sort order is descending."""
        return self.sort_order.lower() == "desc"


class DateRangeParams(BaseModel):
    """Date range filter parameters."""
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
