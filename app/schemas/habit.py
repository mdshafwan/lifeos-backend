"""Pydantic schemas for Habit endpoints."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.models.habit import HabitFrequency, HabitCategory


class HabitBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: str = Field(default="#10b981", max_length=20)
    category: HabitCategory = HabitCategory.OTHER
    frequency: HabitFrequency = HabitFrequency.DAILY
    target_count: int = Field(default=1, ge=1)
    unit: Optional[str] = None
    start_date: Optional[date] = None
    reminder_time: Optional[str] = None
    is_active: bool = True


class HabitCreate(HabitBase):
    pass


class HabitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    category: Optional[HabitCategory] = None
    frequency: Optional[HabitFrequency] = None
    target_count: Optional[int] = Field(None, ge=1)
    unit: Optional[str] = None
    start_date: Optional[date] = None
    reminder_time: Optional[str] = None
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None


class HabitResponse(HabitBase):
    id: int
    user_id: int
    current_streak: int
    longest_streak: int
    total_completions: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    completed_today: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class HabitCompletionCreate(BaseModel):
    completion_date: Optional[date] = None  # defaults to today
    count: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class HabitCompletionResponse(BaseModel):
    id: int
    habit_id: int
    user_id: int
    completion_date: date
    count: int
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HabitListResponse(BaseModel):
    items: List[HabitResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool