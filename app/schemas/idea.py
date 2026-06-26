from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.idea import IdeaCategory, IdeaStatus


class IdeaBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(..., min_length=1)
    category: IdeaCategory = IdeaCategory.OTHER
    tags: List[str] = Field(default_factory=list)
    status: IdeaStatus = IdeaStatus.NEW
    impact_score: int = Field(default=5, ge=1, le=10)
    effort_score: int = Field(default=5, ge=1, le=10)
    confidence_score: int = Field(default=5, ge=1, le=10)
    problem_solved: Optional[str] = None
    target_audience: Optional[str] = None
    resources_needed: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    is_favorite: bool = False


class IdeaCreate(IdeaBase):
    pass


class IdeaUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[IdeaCategory] = None
    status: Optional[IdeaStatus] = None
    impact_score: Optional[int] = None
    effort_score: Optional[int] = None
    confidence_score: Optional[int] = None
    notes: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None


class IdeaResponse(IdeaBase):
    id: int
    user_id: int
    priority_score: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class IdeaListResponse(BaseModel):
    items: List[IdeaResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool