"""
Pydantic schemas for Task endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskPriority, TaskStatus


# ════════════════════════════════════════════════════════════════
# BASE SCHEMA (shared fields)
# ════════════════════════════════════════════════════════════════

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_date: Optional[datetime] = None
    reminder_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = Field(None, ge=0)
    tags: List[str] = Field(default_factory=list)
    subtasks: List[dict] = Field(default_factory=list)
    is_starred: bool = False
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    project_id: Optional[int] = None


# ════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ════════════════════════════════════════════════════════════════

class TaskCreate(TaskBase):
    """Schema for creating a task."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "title": "Build authentication system",
            "description": "Implement JWT-based auth with refresh tokens",
            "priority": "high",
            "status": "todo",
            "tags": ["backend", "security"],
            "estimated_minutes": 120
        }
    })


class TaskUpdate(BaseModel):
    """Schema for updating a task (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    reminder_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = Field(None, ge=0)
    actual_minutes: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    subtasks: Optional[List[dict]] = None
    is_starred: Optional[bool] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    project_id: Optional[int] = None


# ════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ════════════════════════════════════════════════════════════════

class TaskResponse(TaskBase):
    """Schema for task responses."""
    id: int
    user_id: int
    actual_minutes: Optional[int] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool