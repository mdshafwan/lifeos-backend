"""
JournalEntry model — daily journaling with mood tracking.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, Date, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class MoodLevel(str, enum.Enum):
    TERRIBLE = "terrible"      # 1
    BAD = "bad"                # 2
    OKAY = "okay"              # 3
    GOOD = "good"              # 4
    AMAZING = "amazing"        # 5


class WeatherType(str, enum.Enum):
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    SNOWY = "snowy"
    STORMY = "stormy"
    FOGGY = "foggy"


class JournalEntry(BaseModel):
    __tablename__ = "journal_entries"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    entry_date = Column(Date, nullable=False, index=True)
    title = Column(String(300), nullable=True)
    content = Column(Text, nullable=False)

    # ── Mood & Feelings ───────────────────────────────
    mood = Column(Enum(MoodLevel), nullable=True)
    mood_score = Column(Integer, nullable=True)  # 1-10
    energy_level = Column(Integer, nullable=True)  # 1-10
    stress_level = Column(Integer, nullable=True)  # 1-10

    # ── Reflection Prompts ────────────────────────────
    gratitude = Column(JSON, default=list, nullable=False)      # ["family", "health"]
    intentions = Column(JSON, default=list, nullable=False)     # ["focus on deep work"]
    accomplishments = Column(JSON, default=list, nullable=False) # ["finished chapter 3"]
    lessons_learned = Column(Text, nullable=True)

    # ── Context ───────────────────────────────────────
    weather = Column(Enum(WeatherType), nullable=True)
    location = Column(String(200), nullable=True)
    tags = Column(JSON, default=list, nullable=False)

    # ── Flags ─────────────────────────────────────────
    is_private = Column(Boolean, default=True, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="journal_entries")

    def __repr__(self):
        return f"<JournalEntry(id={self.id}, date={self.entry_date}, mood='{self.mood}')>"