"""
Idea model — capture ideas with impact/effort scoring.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class IdeaCategory(str, enum.Enum):
    BUSINESS = "business"
    PRODUCT = "product"
    CONTENT = "content"
    PROJECT = "project"
    INNOVATION = "innovation"
    PERSONAL = "personal"
    OTHER = "other"


class IdeaStatus(str, enum.Enum):
    NEW = "new"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    IN_DEVELOPMENT = "in_development"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"


class Idea(BaseModel):
    __tablename__ = "ideas"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)

    # ── Categorization ────────────────────────────────
    category = Column(Enum(IdeaCategory), default=IdeaCategory.OTHER, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    status = Column(Enum(IdeaStatus), default=IdeaStatus.NEW, nullable=False)

    # ── Scoring (1-10) ────────────────────────────────
    impact_score = Column(Integer, default=5, nullable=False)   # How big the payoff
    effort_score = Column(Integer, default=5, nullable=False)   # How much work
    confidence_score = Column(Integer, default=5, nullable=False)  # How sure it works
    priority_score = Column(Integer, default=0, nullable=False)    # Calculated: impact / effort

    # ── Details ───────────────────────────────────────
    problem_solved = Column(Text, nullable=True)       # What problem does this solve?
    target_audience = Column(String(300), nullable=True)
    resources_needed = Column(JSON, default=list, nullable=False)
    risks = Column(JSON, default=list, nullable=False)
    notes = Column(Text, nullable=True)

    # ── Flags ─────────────────────────────────────────
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="ideas")

    def __repr__(self):
        return f"<Idea(id={self.id}, title='{self.title}', status='{self.status}')>"