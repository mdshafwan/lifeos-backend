"""
Project model — groups related tasks together.
e.g., "Build LifeOS App", "Learn Python", "Renovate House"
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Project(BaseModel):
    __tablename__ = "projects"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(20), default="#3b82f6", nullable=False)  # Hex color
    icon = Column(String(50), nullable=True)  # Emoji or icon name

    # ── Status & Progress ─────────────────────────────
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    progress = Column(Integer, default=0, nullable=False)  # 0-100%

    # ── Dates ─────────────────────────────────────────
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    completed_at = Column(Date, nullable=True)

    # ── Flags ─────────────────────────────────────────
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"