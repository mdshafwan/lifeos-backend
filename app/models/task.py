"""
Task model — individual to-do items.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Date, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    __tablename__ = "tasks"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)

    # ── Core Fields ───────────────────────────────────
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)

    # ── Priority & Status ─────────────────────────────
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False, index=True)

    # ── Dates ─────────────────────────────────────────
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    reminder_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Tracking ──────────────────────────────────────
    estimated_minutes = Column(Integer, nullable=True)  # How long it should take
    actual_minutes = Column(Integer, nullable=True)     # How long it actually took

    # ── Tags & Subtasks (stored as JSON for flexibility) ──
    tags = Column(JSON, default=list, nullable=False)        # ["work", "urgent"]
    subtasks = Column(JSON, default=list, nullable=False)    # [{"title": "...", "done": false}]

    # ── Flags ─────────────────────────────────────────
    is_starred = Column(Boolean, default=False, nullable=False)
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_pattern = Column(String(50), nullable=True)  # "daily", "weekly", "monthly"

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="tasks")
    project = relationship("Project", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"