"""
Import all models here so SQLAlchemy knows about them.

WHY?
- SQLAlchemy relationships reference models by STRING name (e.g., "Project")
- When a relationship is initialized, SQLAlchemy needs the class to exist
- Importing all models here ensures they're registered with the Base metadata
- This file runs whenever you `from app.models import ...`
"""

# ── Core ──
from app.models.base import BaseModel
from app.models.user import User

# ── Productivity ──
from app.models.project import Project
from app.models.task import Task
from app.models.habit import Habit, HabitCompletion
from app.models.goal import Goal, Milestone
from app.models.calendar_event import CalendarEvent

# ── Knowledge ──
from app.models.note import Note
from app.models.journal import JournalEntry
from app.models.wiki import Wiki
from app.models.learning import Learning
from app.models.idea import Idea

# ── Life ──
from app.models.health import HealthLog
from app.models.finance import FinancialAccount, Transaction
from app.models.vision_board import VisionBoard

# ── Business ──
from app.models.business import Business
from app.models.contact import Contact
from app.models.document import Document

# ── Gamification ──
from app.models.achievement import Achievement, UserAchievement
from app.models.notification import Notification
from app.models.ai_chat import AIChat, AIMessage

from app.models.otp import OTPCode


# Export all models for easy importing
__all__ = [
    "BaseModel",
    "User",
    "Project",
    "Task",
    "Habit",
    "HabitCompletion",
    "Goal",
    "Milestone",
    "CalendarEvent",
    "Note",
    "JournalEntry",
    "Wiki",
    "Learning",
    "Idea",
    "HealthLog",
    "FinancialAccount",
    "Transaction",
    "VisionBoard",
    "Business",
    "Contact",
    "Document",
    "Achievement",
    "UserAchievement",
    "Notification",
    "AIChat",
    "AIMessage",
]