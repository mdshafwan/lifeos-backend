"""
VisionBoard model — unified table for vision items, affirmations, letters, goals.
Uses String columns (not Enum) to avoid case-sensitivity issues with PostgreSQL.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


# ── Enum-like constants (used by schemas + frontend) ──────────────
# These are just helpers — NOT SQLAlchemy Enum columns
class VisionCategory(str, enum.Enum):
    CAREER = "career"
    HEALTH = "health"
    RELATIONSHIPS = "relationships"
    WEALTH = "wealth"
    GROWTH = "growth"
    TRAVEL = "travel"
    CREATIVITY = "creativity"
    SPIRITUALITY = "spirituality"
    FAMILY = "family"
    LIFESTYLE = "lifestyle"
    OTHER = "other"


class VisionItemType(str, enum.Enum):
    """Type of vision board item."""
    IMAGE = "image"
    TEXT = "text"
    AFFIRMATION = "affirmation"
    QUOTE = "quote"
    GOAL = "goal"
    LETTER = "letter"


class VisionItemSize(str, enum.Enum):
    """Display size for vision board cards."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class VisionBoard(BaseModel):
    __tablename__ = "vision_boards"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core ──
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    affirmation = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)  # text for base64 data URLs
    color = Column(String(20), default="#e879f9", nullable=False)

    # ── Type & Display (String, not Enum to avoid PG enum issues) ──
    item_type = Column(String(20), default="image", nullable=False, index=True)
    size = Column(String(20), default="medium", nullable=False)

    # ── Categorization ──
    category = Column(String(50), default="other", nullable=False, index=True)
    tags = Column(JSON, default=list, nullable=False)

    # ── Dates ──
    target_date = Column(Date, nullable=True)
    achieved_at = Column(Date, nullable=True)

    # ── Position (board layout) ──
    position_x = Column(Integer, default=0, nullable=False)
    position_y = Column(Integer, default=0, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)

    # ── Flags ──
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_achieved = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # ── Letter-specific ──
    mood = Column(String(50), nullable=True)            # inspired/grateful/etc
    delivery_date = Column(Date, nullable=True)         # when letter unlocks
    is_sealed = Column(Boolean, default=False, nullable=False)

    # ── Goal-specific ──
    progress = Column(Integer, default=0, nullable=False)   # 0-100
    milestones = Column(JSON, default=list, nullable=False) # [{text, done}]

    # ── Image-specific ──
    image_source = Column(String(20), nullable=True)    # 'url' or 'upload'

    # ── Relationships ──
    user = relationship("User", backref="vision_board_items")

    def __repr__(self):
        return f"<VisionBoard(id={self.id}, type='{self.item_type}', title='{self.title}')>"