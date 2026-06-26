from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.calendar_event import EventType, RecurrenceType


class CalendarEventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    event_type: EventType = EventType.OTHER
    color: str = "#3b82f6"
    recurrence: RecurrenceType = RecurrenceType.NONE
    recurrence_end_date: Optional[datetime] = None
    reminder_minutes_before: Optional[int] = None
    meeting_url: Optional[str] = None


class CalendarEventCreate(CalendarEventBase):
    pass


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    event_type: Optional[EventType] = None
    color: Optional[str] = None
    recurrence: Optional[RecurrenceType] = None
    reminder_minutes_before: Optional[int] = None
    meeting_url: Optional[str] = None
    is_completed: Optional[bool] = None


class CalendarEventResponse(CalendarEventBase):
    id: int
    user_id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CalendarEventListResponse(BaseModel):
    items: List[CalendarEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool