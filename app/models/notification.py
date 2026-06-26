"""
Notification model — in-app notifications for users.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class NotificationType(str, enum.Enum):
    REMINDER = "reminder"
    ACHIEVEMENT = "achievement"
    STREAK = "streak"
    LEVEL_UP = "level_up"
    DEADLINE = "deadline"
    GOAL_MILESTONE = "goal_milestone"
    HABIT_REMINDER = "habit_reminder"
    BIRTHDAY = "birthday"
    SYSTEM = "system"
    AI_INSIGHT = "ai_insight"
    OTHER = "other"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), default=NotificationType.SYSTEM, nullable=False, index=True)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False)

    # ── Visual ────────────────────────────────────────
    icon = Column(String(100), nullable=True)
    color = Column(String(20), default="#3b82f6", nullable=False)

    # ── Action ────────────────────────────────────────
    action_url = Column(String(500), nullable=True)        # Where to navigate when clicked
    action_label = Column(String(100), nullable=True)      # "View Task", "Open Goal"

    # ── Related Entity (polymorphic) ──────────────────
    related_entity_type = Column(String(50), nullable=True)  # "task", "goal", "habit"
    related_entity_id = Column(Integer, nullable=True)

    # ── Metadata ──────────────────────────────────────
    extra_data = Column(JSON, default=dict, nullable=False)

    # ── Status ────────────────────────────────────────
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # ── Scheduling ────────────────────────────────────
    scheduled_for = Column(DateTime(timezone=True), nullable=True, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, title='{self.title}', read={self.is_read})>"