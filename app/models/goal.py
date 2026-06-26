"""
Goal + Milestone models — long-term goals with checkpoints.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, Date, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class GoalCategory(str, enum.Enum):
    CAREER = "career"
    HEALTH = "health"
    FINANCE = "finance"
    LEARNING = "learning"
    RELATIONSHIPS = "relationships"
    PERSONAL = "personal"
    CREATIVE = "creative"
    SPIRITUAL = "spiritual"
    OTHER = "other"


class GoalStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class GoalPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Goal(BaseModel):
    __tablename__ = "goals"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    why = Column(Text, nullable=True)  # Why this goal matters (motivation)

    # ── Categorization ────────────────────────────────
    category = Column(Enum(GoalCategory), default=GoalCategory.PERSONAL, nullable=False)
    priority = Column(Enum(GoalPriority), default=GoalPriority.MEDIUM, nullable=False)
    status = Column(Enum(GoalStatus), default=GoalStatus.NOT_STARTED, nullable=False)

    # ── Progress ──────────────────────────────────────
    progress = Column(Integer, default=0, nullable=False)  # 0-100%
    target_value = Column(Float, nullable=True)             # e.g., 100 (kg, $, books)
    current_value = Column(Float, default=0, nullable=False)
    unit = Column(String(50), nullable=True)                # "kg", "$", "books"

    # ── Dates ─────────────────────────────────────────
    start_date = Column(Date, nullable=True)
    target_date = Column(Date, nullable=True)
    completed_at = Column(Date, nullable=True)

    # ── Visual ────────────────────────────────────────
    color = Column(String(20), default="#8b5cf6", nullable=False)
    icon = Column(String(50), nullable=True)

    # ── Flags ─────────────────────────────────────────
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="goals")
    milestones = relationship("Milestone", back_populates="goal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Goal(id={self.id}, title='{self.title}', progress={self.progress}%)>"


class Milestone(BaseModel):
    """Sub-goals or checkpoints within a Goal."""
    __tablename__ = "milestones"

    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(Date, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(Date, nullable=True)
    order_index = Column(Integer, default=0, nullable=False)  # For sorting

    # ── Relationships ─────────────────────────────────
    goal = relationship("Goal", back_populates="milestones")

    def __repr__(self):
        return f"<Milestone(id={self.id}, title='{self.title}', completed={self.is_completed})>"