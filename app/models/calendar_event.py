"""
CalendarEvent model — events with recurrence support.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class EventType(str, enum.Enum):
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    BIRTHDAY = "birthday"
    HOLIDAY = "holiday"
    WORK = "work"
    PERSONAL = "personal"
    OTHER = "other"


class RecurrenceType(str, enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class CalendarEvent(BaseModel):
    __tablename__ = "calendar_events"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(300), nullable=True)

    # ── Time ──────────────────────────────────────────
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    is_all_day = Column(Boolean, default=False, nullable=False)

    # ── Categorization ────────────────────────────────
    event_type = Column(Enum(EventType), default=EventType.OTHER, nullable=False)
    color = Column(String(20), default="#3b82f6", nullable=False)

    # ── Recurrence ────────────────────────────────────
    recurrence = Column(Enum(RecurrenceType), default=RecurrenceType.NONE, nullable=False)
    recurrence_end_date = Column(DateTime(timezone=True), nullable=True)

    # ── Reminder ──────────────────────────────────────
    reminder_minutes_before = Column(Integer, nullable=True)  # 15, 30, 60, etc.

    # ── Meeting Link ──────────────────────────────────
    meeting_url = Column(String(500), nullable=True)

    # ── Flags ─────────────────────────────────────────
    is_completed = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="calendar_events")

    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title='{self.title}', start={self.start_time})>"