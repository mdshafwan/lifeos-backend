from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class WikiBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    slug: str = Field(..., min_length=1, max_length=300)
    content: str
    excerpt: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    parent_id: Optional[int] = None
    is_published: bool = False
    is_favorite: bool = False


class WikiCreate(WikiBase): pass


class WikiUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None
    is_favorite: Optional[bool] = None


class WikiResponse(WikiBase):
    id: int
    user_id: int
    view_count: int
    word_count: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WikiListResponse(BaseModel):
    items: List[WikiResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool