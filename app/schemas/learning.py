from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.models.learning import LearningType, LearningStatus


class LearningBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    instructor: Optional[str] = None
    provider: Optional[str] = None
    url: Optional[str] = None
    learning_type: LearningType = LearningType.COURSE
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    status: LearningStatus = LearningStatus.WISHLIST
    progress: int = Field(default=0, ge=0, le=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    total_hours: Optional[float] = None
    hours_spent: float = 0
    start_date: Optional[date] = None
    completed_date: Optional[date] = None
    cost: Optional[float] = None
    currency: str = "USD"
    notes: Optional[str] = None
    key_takeaways: List[str] = Field(default_factory=list)
    certificate_url: Optional[str] = None
    is_favorite: bool = False


class LearningCreate(LearningBase): pass


class LearningUpdate(BaseModel):
    # ── Core ──
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    instructor: Optional[str] = None
    provider: Optional[str] = None
    url: Optional[str] = None
    
    # ── Categorization ──
    learning_type: Optional[LearningType] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    
    # ── Status & Progress ──
    status: Optional[LearningStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    
    # ── Time ──
    total_hours: Optional[float] = None
    hours_spent: Optional[float] = None
    
    # ── Dates ──
    start_date: Optional[date] = None
    completed_date: Optional[date] = None
    
    # ── Cost ──
    cost: Optional[float] = None
    currency: Optional[str] = None
    
    # ── Notes & Files ──
    notes: Optional[str] = None
    key_takeaways: Optional[List[str]] = None
    certificate_url: Optional[str] = None
    
    # ── Flags ──
    is_favorite: Optional[bool] = None


class LearningResponse(LearningBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LearningListResponse(BaseModel):
    items: List[LearningResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool