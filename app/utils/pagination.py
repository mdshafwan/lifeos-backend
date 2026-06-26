"""
Pagination utility — standardize how lists are returned.

WHY?
- Frontend can show pagination controls
- Prevents loading 10,000 items at once
- Consistent response shape across all endpoints
"""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional
from sqlalchemy.orm import Query
from math import ceil


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def paginate(query: Query, page: int = 1, page_size: int = 20) -> dict:
    """
    Apply pagination to a SQLAlchemy query.
    
    Returns a dict suitable for PaginatedResponse.
    """
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }