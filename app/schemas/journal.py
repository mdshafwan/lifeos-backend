"""Pydantic schemas for Journal."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.models.journal import MoodLevel, WeatherType


class JournalBase(BaseModel):
    entry_date: date
    title: Optional[str] = None
    content: str = Field(..., min_length=1)
    mood: Optional[MoodLevel] = None
    mood_score: Optional[int] = Field(None, ge=1, le=10)
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    gratitude: List[str] = Field(default_factory=list)
    intentions: List[str] = Field(default_factory=list)
    accomplishments: List[str] = Field(default_factory=list)
    lessons_learned: Optional[str] = None
    weather: Optional[WeatherType] = None
    location: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_private: bool = True
    is_favorite: bool = False


class JournalCreate(JournalBase):
    pass


class JournalUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood: Optional[MoodLevel] = None
    mood_score: Optional[int] = None
    energy_level: Optional[int] = None
    stress_level: Optional[int] = None
    gratitude: Optional[List[str]] = None
    intentions: Optional[List[str]] = None
    accomplishments: Optional[List[str]] = None
    lessons_learned: Optional[str] = None
    weather: Optional[WeatherType] = None
    location: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None


class JournalResponse(JournalBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JournalListResponse(BaseModel):
    items: List[JournalResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool