"""
Achievement system:
- Achievement: The badge definition (system-defined templates)
- UserAchievement: Tracks which achievements each user has unlocked

WHY two tables?
- Achievements are shared (same definitions for all users)
- UserAchievement tracks who unlocked what + when
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class AchievementCategory(str, enum.Enum):
    TASKS = "tasks"
    HABITS = "habits"
    GOALS = "goals"
    JOURNAL = "journal"
    HEALTH = "health"
    FINANCE = "finance"
    LEARNING = "learning"
    STREAK = "streak"
    MILESTONE = "milestone"
    SPECIAL = "special"


class AchievementRarity(str, enum.Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class Achievement(BaseModel):
    """The badge definition (template)."""
    __tablename__ = "achievements"

    # ── Core Fields ───────────────────────────────────
    code = Column(String(100), unique=True, nullable=False, index=True)  # "first_task", "30_day_streak"
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # ── Visual ────────────────────────────────────────
    icon = Column(String(100), nullable=True)        # Icon name or emoji
    badge_color = Column(String(20), default="#fbbf24", nullable=False)
    image_url = Column(String(500), nullable=True)

    # ── Categorization ────────────────────────────────
    category = Column(Enum(AchievementCategory), default=AchievementCategory.SPECIAL, nullable=False, index=True)
    rarity = Column(Enum(AchievementRarity), default=AchievementRarity.COMMON, nullable=False)

    # ── Rewards ───────────────────────────────────────
    xp_reward = Column(Integer, default=50, nullable=False)

    # ── Unlock Criteria ───────────────────────────────
    criteria_type = Column(String(100), nullable=False)  # "task_count", "streak_days", "goal_completed"
    criteria_value = Column(Integer, default=1, nullable=False)  # Required count

    # ── Flags ─────────────────────────────────────────
    is_active = Column(Boolean, default=True, nullable=False)
    is_hidden = Column(Boolean, default=False, nullable=False)  # Hidden until unlocked

    # ── Relationships ─────────────────────────────────
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Achievement(code='{self.code}', name='{self.name}')>"


class UserAchievement(BaseModel):
    """Tracks which user has unlocked which achievement."""
    __tablename__ = "user_achievements"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Unlock Info ───────────────────────────────────
    unlocked_at = Column(DateTime(timezone=True), nullable=False)
    progress = Column(Integer, default=0, nullable=False)  # Current progress
    is_seen = Column(Boolean, default=False, nullable=False)  # Has user seen the unlock notification?

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="user_achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

    # ── Constraints ───────────────────────────────────
    # One user can't unlock the same achievement twice
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )

    def __repr__(self):
        return f"<UserAchievement(user_id={self.user_id}, achievement_id={self.achievement_id})>"