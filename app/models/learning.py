"""
Learning model — track courses, books, tutorials.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, Date, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class LearningType(str, enum.Enum):
    COURSE = "course"
    BOOK = "book"
    TUTORIAL = "tutorial"
    VIDEO = "video"
    PODCAST = "podcast"
    ARTICLE = "article"
    WORKSHOP = "workshop"
    CERTIFICATION = "certification"
    OTHER = "other"


class LearningStatus(str, enum.Enum):
    WISHLIST = "wishlist"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class Learning(BaseModel):
    __tablename__ = "learnings"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    instructor = Column(String(200), nullable=True)
    provider = Column(String(200), nullable=True)  # Udemy, Coursera, etc.
    url = Column(String(500), nullable=True)

    # ── Categorization ────────────────────────────────
    learning_type = Column(Enum(LearningType), default=LearningType.COURSE, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, default=list, nullable=False)
    skills = Column(JSON, default=list, nullable=False)  # ["Python", "FastAPI"]

    # ── Status & Progress ─────────────────────────────
    status = Column(Enum(LearningStatus), default=LearningStatus.WISHLIST, nullable=False)
    progress = Column(Integer, default=0, nullable=False)  # 0-100%
    rating = Column(Integer, nullable=True)  # 1-5 stars

    # ── Time Tracking ─────────────────────────────────
    total_hours = Column(Float, nullable=True)
    hours_spent = Column(Float, default=0, nullable=False)

    # ── Dates ─────────────────────────────────────────
    start_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)

    # ── Cost ──────────────────────────────────────────
    cost = Column(Float, nullable=True)
    currency = Column(String(10), default="USD", nullable=True)

    # ── Notes ─────────────────────────────────────────
    notes = Column(Text, nullable=True)
    key_takeaways = Column(JSON, default=list, nullable=False)
    certificate_url = Column(String(500), nullable=True)

    # ── Flags ─────────────────────────────────────────
    is_favorite = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="learnings")

    def __repr__(self):
        return f"<Learning(id={self.id}, title='{self.title}', status='{self.status}')>"