"""Pydantic schemas for Goals + Milestones."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.models.goal import GoalCategory, GoalStatus, GoalPriority


class MilestoneBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    target_date: Optional[date] = None
    order_index: int = 0


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[date] = None
    is_completed: Optional[bool] = None
    order_index: Optional[int] = None


class MilestoneResponse(MilestoneBase):
    id: int
    goal_id: int
    is_completed: bool
    completed_at: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    why: Optional[str] = None
    category: GoalCategory = GoalCategory.PERSONAL
    priority: GoalPriority = GoalPriority.MEDIUM
    status: GoalStatus = GoalStatus.NOT_STARTED
    progress: int = Field(default=0, ge=0, le=100)
    target_value: Optional[float] = None
    current_value: float = 0
    unit: Optional[str] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    color: str = "#8b5cf6"
    icon: Optional[str] = None
    is_favorite: bool = False


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    why: Optional[str] = None
    category: Optional[GoalCategory] = None
    priority: Optional[GoalPriority] = None
    status: Optional[GoalStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    unit: Optional[str] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None


class GoalResponse(GoalBase):
    id: int
    user_id: int
    completed_at: Optional[date] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    milestones: List[MilestoneResponse] = []

    model_config = ConfigDict(from_attributes=True)


class GoalListResponse(BaseModel):
    items: List[GoalResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool