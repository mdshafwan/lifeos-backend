"""Gamification API — XP, levels, achievements, notifications."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.models.achievement import Achievement, UserAchievement
from app.models.notification import Notification, NotificationType
from app.schemas.gamification import (
    AchievementResponse, UserAchievementResponse,
    NotificationResponse, GamificationStats, XPInfo,
)
from app.core.dependencies import get_current_user
from app.services.gamification_service import GamificationService

router = APIRouter()


# ════════════════════════════════════════════════════════════════
# STATS
# ════════════════════════════════════════════════════════════════

@router.get("/stats", response_model=GamificationStats, summary="Get user gamification stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get complete gamification overview for current user."""
    xp_info = GamificationService.xp_for_next_level(current_user.xp)
    
    total_ach = db.query(Achievement).filter(Achievement.is_active == True).count()
    unlocked_ach = db.query(UserAchievement).filter(UserAchievement.user_id == current_user.id).count()
    unread = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).count()
    
    return GamificationStats(
        user_id=current_user.id,
        xp=current_user.xp,
        level=current_user.level,
        life_score=current_user.life_score,
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
        xp_info=XPInfo(**xp_info),
        total_achievements=total_ach,
        unlocked_achievements=unlocked_ach,
        unread_notifications=unread,
    )


@router.post("/refresh-life-score", summary="Recalculate life score")
async def refresh_life_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a recalculation of the life score."""
    service = GamificationService(db, current_user)
    score = service.calculate_life_score()
    return {"life_score": score, "message": "Life score updated"}


@router.post("/check-in", summary="Daily check-in for streak XP")
async def daily_checkin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update daily streak and award login XP."""
    service = GamificationService(db, current_user)
    result = service.update_login_streak()
    service.check_achievements()
    return result


# ════════════════════════════════════════════════════════════════
# ACHIEVEMENTS
# ════════════════════════════════════════════════════════════════

@router.get("/achievements", response_model=List[AchievementResponse], summary="List all achievements")
async def list_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List ALL system achievements (visible to all users)."""
    return db.query(Achievement).filter(Achievement.is_active == True).all()


@router.get("/achievements/unlocked", response_model=List[UserAchievementResponse], summary="List user's unlocked achievements")
async def list_unlocked_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List achievements unlocked by current user."""
    return db.query(UserAchievement).options(
        joinedload(UserAchievement.achievement)
    ).filter(
        UserAchievement.user_id == current_user.id
    ).order_by(desc(UserAchievement.unlocked_at)).all()


@router.post("/achievements/check", summary="Manually check for achievement unlocks")
async def check_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger achievement check (usually called automatically)."""
    service = GamificationService(db, current_user)
    newly_unlocked = service.check_achievements()
    return {
        "newly_unlocked_count": len(newly_unlocked),
        "newly_unlocked": [
            {"name": u.achievement.name, "xp_reward": u.achievement.xp_reward}
            for u in newly_unlocked
        ]
    }


@router.post("/achievements/{achievement_id}/mark-seen", summary="Mark achievement as seen")
async def mark_achievement_seen(
    achievement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark an unlocked achievement as seen (dismiss notification)."""
    user_ach = db.query(UserAchievement).filter(
        UserAchievement.user_id == current_user.id,
        UserAchievement.achievement_id == achievement_id,
    ).first()
    if not user_ach:
        raise HTTPException(404, "Achievement not unlocked")
    user_ach.is_seen = True
    db.commit()
    return {"message": "Marked as seen"}


# ════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ════════════════════════════════════════════════════════════════

@router.get("/notifications", response_model=List[NotificationResponse], summary="List notifications")
async def list_notifications(
    is_read: Optional[bool] = Query(None),
    notification_type: Optional[NotificationType] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's notifications."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    return query.order_by(desc(Notification.created_at)).limit(limit).all()


@router.post("/notifications/{notif_id}/read", summary="Mark notification as read")
async def mark_notification_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a single notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(404, "Notification not found")
    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Marked as read"}


@router.post("/notifications/read-all", summary="Mark all notifications as read")
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark ALL user's notifications as read."""
    updated = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({
        "is_read": True,
        "read_at": datetime.now(timezone.utc),
    })
    db.commit()
    return {"marked_read_count": updated}


@router.delete("/notifications/{notif_id}", status_code=204, summary="Delete notification")
async def delete_notification(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(404, "Notification not found")
    db.delete(notif)
    db.commit()
    return None


# ════════════════════════════════════════════════════════════════
# LEADERBOARD (BONUS!)
# ════════════════════════════════════════════════════════════════

@router.get("/leaderboard", summary="Top users by XP")
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get top users by XP (gamification competition)."""
    top_users = db.query(User).filter(User.is_active == True).order_by(desc(User.xp)).limit(limit).all()
    return [
        {
            "rank": i + 1,
            "username": u.username,
            "level": u.level,
            "xp": u.xp,
            "life_score": u.life_score,
            "current_streak": u.current_streak,
            "is_you": u.id == current_user.id,
        }
        for i, u in enumerate(top_users)
    ]