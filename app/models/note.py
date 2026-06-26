"""
Note model — quick notes with tags, pin, favorite.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class NoteColor(str, enum.Enum):
    DEFAULT = "default"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    RED = "red"
    PURPLE = "purple"
    ORANGE = "orange"
    PINK = "pink"


class Note(BaseModel):
    __tablename__ = "notes"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    title = Column(String(300), nullable=True)
    content = Column(Text, nullable=False)

    # ── Organization ──────────────────────────────────
    folder = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, default=list, nullable=False)  # ["work", "ideas"]

    # ── Visual ────────────────────────────────────────
    color = Column(Enum(NoteColor), default=NoteColor.DEFAULT, nullable=False)

    # ── Flags ─────────────────────────────────────────
    is_pinned = Column(Boolean, default=False, nullable=False, index=True)
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # ── Rich Content (optional) ───────────────────────
    attachments = Column(JSON, default=list, nullable=False)  # File URLs

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="notes")

    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}')>"