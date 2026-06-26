"""Pydantic schemas for gamification."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.achievement import AchievementCategory, AchievementRarity
from app.models.notification import NotificationType, NotificationPriority


# ── ACHIEVEMENTS ──
class AchievementResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str
    icon: Optional[str] = None
    badge_color: str
    image_url: Optional[str] = None
    category: AchievementCategory
    rarity: AchievementRarity
    xp_reward: int
    criteria_type: str
    criteria_value: int
    is_hidden: bool
    model_config = ConfigDict(from_attributes=True)


class UserAchievementResponse(BaseModel):
    id: int
    achievement: AchievementResponse
    unlocked_at: datetime
    progress: int
    is_seen: bool
    model_config = ConfigDict(from_attributes=True)


# ── NOTIFICATIONS ──
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority
    icon: Optional[str] = None
    color: str
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── STATS / DASHBOARD ──
class XPInfo(BaseModel):
    current_level: int
    current_xp: int
    next_level: int
    xp_for_next_level: int
    xp_needed: int
    progress_percentage: int


class GamificationStats(BaseModel):
    user_id: int
    xp: int
    level: int
    life_score: int
    current_streak: int
    longest_streak: int
    xp_info: XPInfo
    total_achievements: int
    unlocked_achievements: int
    unread_notifications: int