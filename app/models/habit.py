"""
Habit + HabitCompletion models — track daily habits & streaks.

Two tables:
- habits: The habit definition (e.g., "Drink 8 glasses of water")
- habit_completions: Logs of when the habit was completed
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, Date, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class HabitFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class HabitCategory(str, enum.Enum):
    HEALTH = "health"
    FITNESS = "fitness"
    MINDFULNESS = "mindfulness"
    LEARNING = "learning"
    PRODUCTIVITY = "productivity"
    SOCIAL = "social"
    CREATIVE = "creative"
    FINANCE = "finance"
    OTHER = "other"


class Habit(BaseModel):
    __tablename__ = "habits"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(20), default="#10b981", nullable=False)

    # ── Categorization ────────────────────────────────
    category = Column(Enum(HabitCategory), default=HabitCategory.OTHER, nullable=False)
    frequency = Column(Enum(HabitFrequency), default=HabitFrequency.DAILY, nullable=False)
    target_count = Column(Integer, default=1, nullable=False)  # e.g., 8 glasses of water
    unit = Column(String(50), nullable=True)                    # "glasses", "minutes", "pages"

    # ── Streak Tracking ───────────────────────────────
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    total_completions = Column(Integer, default=0, nullable=False)

    # ── Dates ─────────────────────────────────────────
    start_date = Column(Date, nullable=True)
    reminder_time = Column(String(10), nullable=True)  # "08:00"

    # ── Flags ─────────────────────────────────────────
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="habits")
    completions = relationship("HabitCompletion", back_populates="habit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Habit(id={self.id}, name='{self.name}', streak={self.current_streak})>"


class HabitCompletion(BaseModel):
    """Logs each time a habit is completed."""
    __tablename__ = "habit_completions"

    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    completion_date = Column(Date, nullable=False, index=True)
    count = Column(Integer, default=1, nullable=False)  # How many times completed today
    notes = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────
    habit = relationship("Habit", back_populates="completions")

    # ── Constraints ───────────────────────────────────
    # One completion entry per habit per day
    __table_args__ = (
        UniqueConstraint("habit_id", "completion_date", name="uq_habit_date"),
    )

    def __repr__(self):
        return f"<HabitCompletion(habit_id={self.habit_id}, date={self.completion_date})>"