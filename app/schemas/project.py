"""Pydantic schemas for Project endpoints."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    color: str = Field(default="#3b82f6", max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    status: ProjectStatus = ProjectStatus.ACTIVE
    progress: int = Field(default=0, ge=0, le=100)
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    is_favorite: bool = False
    is_archived: bool = False


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[ProjectStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    completed_at: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    task_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool