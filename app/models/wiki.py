"""
Wiki model — personal knowledge base articles.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Wiki(BaseModel):
    __tablename__ = "wikis"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("wikis.id", ondelete="SET NULL"), nullable=True, index=True)

    # ── Core Fields ───────────────────────────────────
    title = Column(String(300), nullable=False)
    slug = Column(String(300), nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(String(500), nullable=True)

    # ── Organization ──────────────────────────────────
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, default=list, nullable=False)

    # ── Stats ─────────────────────────────────────────
    view_count = Column(Integer, default=0, nullable=False)
    word_count = Column(Integer, default=0, nullable=False)

    # ── Flags ─────────────────────────────────────────
    is_published = Column(Boolean, default=False, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="wikis")
    parent = relationship("Wiki", remote_side="Wiki.id", backref="children")

    def __repr__(self):
        return f"<Wiki(id={self.id}, title='{self.title}')>"