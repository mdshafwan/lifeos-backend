"""
Gamification service — XP, levels, achievements, streaks.

The HEART of the gamification system. Every user action that should
award XP goes through this service.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any
from loguru import logger

from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.habit import Habit, HabitCompletion
from app.models.goal import Goal, GoalStatus
from app.models.journal import JournalEntry
from app.models.achievement import Achievement, UserAchievement
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.config import settings


class GamificationService:
    """Centralized gamification logic."""

    # ════════════════════════════════════════════════════════════
    # LEVEL CALCULATION
    # ════════════════════════════════════════════════════════════
    
    @staticmethod
    def xp_required_for_level(level: int) -> int:
        """
        Calculate XP needed to reach a level.
        Formula: 100 * level^1.5 (exponential growth)
        
        Level 1: 0 XP
        Level 2: 100 XP
        Level 3: 283 XP
        Level 4: 520 XP
        Level 5: 800 XP
        Level 10: 3,162 XP
        Level 20: 8,944 XP
        Level 50: 35,355 XP
        """
        if level <= 1:
            return 0
        return int(100 * ((level - 1) ** 1.5))

    @staticmethod
    def calculate_level(xp: int) -> int:
        """Determine level from total XP."""
        level = 1
        while GamificationService.xp_required_for_level(level + 1) <= xp:
            level += 1
        return level

    @staticmethod
    def xp_for_next_level(xp: int) -> Dict[str, int]:
        """Get XP needed to reach next level."""
        current_level = GamificationService.calculate_level(xp)
        next_level_xp = GamificationService.xp_required_for_level(current_level + 1)
        current_level_xp = GamificationService.xp_required_for_level(current_level)
        
        return {
            "current_level": current_level,
            "current_xp": xp,
            "next_level": current_level + 1,
            "xp_for_next_level": next_level_xp,
            "xp_needed": next_level_xp - xp,
            "progress_percentage": int(((xp - current_level_xp) / (next_level_xp - current_level_xp)) * 100) if next_level_xp > current_level_xp else 0,
        }

    # ════════════════════════════════════════════════════════════
    # AWARD XP
    # ════════════════════════════════════════════════════════════

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

    def award_xp(self, amount: int, reason: str = "") -> Dict[str, Any]:
        """
        Award XP to the user and handle level-up.
        
        Returns dict with old_level, new_level, leveled_up flag.
        """
        old_level = self.user.level
        old_xp = self.user.xp
        
        self.user.xp += amount
        new_level = self.calculate_level(self.user.xp)
        leveled_up = new_level > old_level
        
        if leveled_up:
            self.user.level = new_level
            self._create_level_up_notification(old_level, new_level)
            logger.info(f"🎉 LEVEL UP! User {self.user.id}: {old_level} → {new_level}")
        
        self.db.commit()
        self.db.refresh(self.user)
        
        logger.info(f"⭐ +{amount} XP awarded to user {self.user.id} ({reason}). Total: {self.user.xp}")
        
        return {
            "xp_awarded": amount,
            "old_xp": old_xp,
            "new_xp": self.user.xp,
            "old_level": old_level,
            "new_level": new_level,
            "leveled_up": leveled_up,
            "reason": reason,
        }

    # ════════════════════════════════════════════════════════════
    # STREAK TRACKING
    # ════════════════════════════════════════════════════════════

    def update_login_streak(self) -> Dict[str, Any]:
        """Update user's daily login streak."""
        today = date.today()
        
        if self.user.last_active_date == today:
            return {"streak": self.user.current_streak, "updated": False, "message": "Already active today"}
        
        if self.user.last_active_date == today - timedelta(days=1):
            # Continued streak
            self.user.current_streak += 1
        elif self.user.last_active_date is None or self.user.last_active_date < today - timedelta(days=1):
            # Broken or first time
            self.user.current_streak = 1
        
        self.user.longest_streak = max(self.user.longest_streak, self.user.current_streak)
        self.user.last_active_date = today
        
        # Award streak XP
        xp_reward = settings.XP_LOGIN_STREAK
        self.award_xp(xp_reward, f"Daily login streak (Day {self.user.current_streak})")
        
        # Check streak milestones
        if self.user.current_streak in [7, 30, 100, 365]:
            self._create_streak_notification(self.user.current_streak)
        
        self.db.commit()
        self.db.refresh(self.user)
        
        return {
            "streak": self.user.current_streak,
            "longest_streak": self.user.longest_streak,
            "updated": True,
            "xp_awarded": xp_reward,
        }

    # ════════════════════════════════════════════════════════════
    # LIFE SCORE
    # ════════════════════════════════════════════════════════════

    def calculate_life_score(self) -> int:
        """
        Calculate user's life score (0-100) based on activity.
        
        Factors:
        - Task completion rate (25%)
        - Habit consistency (25%)
        - Goal progress (20%)
        - Journal frequency (15%)
        - Streak length (15%)
        """
        scores = []
        
        # Tasks (25%)
        total_tasks = self.db.query(Task).filter(Task.user_id == self.user.id).count()
        if total_tasks > 0:
            completed = self.db.query(Task).filter(
                Task.user_id == self.user.id,
                Task.status == TaskStatus.COMPLETED
            ).count()
            scores.append((completed / total_tasks) * 25)
        else:
            scores.append(12.5)  # Neutral
        
        # Habits (25%)
        active_habits = self.db.query(Habit).filter(
            Habit.user_id == self.user.id,
            Habit.is_active == True
        ).count()
        if active_habits > 0:
            recent = date.today() - timedelta(days=7)
            completions = self.db.query(HabitCompletion).filter(
                HabitCompletion.user_id == self.user.id,
                HabitCompletion.completion_date >= recent
            ).count()
            possible = active_habits * 7
            scores.append(min((completions / possible) * 25, 25))
        else:
            scores.append(12.5)
        
        # Goals (20%)
        active_goals = self.db.query(Goal).filter(
            Goal.user_id == self.user.id,
            Goal.status == GoalStatus.IN_PROGRESS
        ).all()
        if active_goals:
            avg_progress = sum(g.progress for g in active_goals) / len(active_goals)
            scores.append((avg_progress / 100) * 20)
        else:
            scores.append(10)
        
        # Journal (15%)
        recent_entries = self.db.query(JournalEntry).filter(
            JournalEntry.user_id == self.user.id,
            JournalEntry.entry_date >= date.today() - timedelta(days=7)
        ).count()
        scores.append(min((recent_entries / 7) * 15, 15))
        
        # Streak (15%)
        streak_score = min((self.user.current_streak / 30) * 15, 15)
        scores.append(streak_score)
        
        total_score = int(sum(scores))
        self.user.life_score = total_score
        self.db.commit()
        
        return total_score

    # ════════════════════════════════════════════════════════════
    # ACHIEVEMENT CHECKING
    # ════════════════════════════════════════════════════════════

    def check_achievements(self) -> List[UserAchievement]:
        """
        Check all achievements and unlock any that the user has earned.
        
        Returns list of newly unlocked achievements.
        """
        newly_unlocked = []
        all_achievements = self.db.query(Achievement).filter(Achievement.is_active == True).all()
        
        for ach in all_achievements:
            # Already unlocked?
            existing = self.db.query(UserAchievement).filter(
                UserAchievement.user_id == self.user.id,
                UserAchievement.achievement_id == ach.id
            ).first()
            if existing:
                continue
            
            # Check criteria
            if self._check_criteria(ach):
                unlock = UserAchievement(
                    user_id=self.user.id,
                    achievement_id=ach.id,
                    unlocked_at=datetime.now(timezone.utc),
                    progress=ach.criteria_value,
                    is_seen=False,
                )
                self.db.add(unlock)
                
                # Award XP
                self.award_xp(ach.xp_reward, f"Achievement: {ach.name}")
                
                # Create notification
                self._create_achievement_notification(ach)
                
                newly_unlocked.append(unlock)
                logger.info(f"🏆 Achievement unlocked: '{ach.name}' for user {self.user.id}")
        
        self.db.commit()
        return newly_unlocked

    def _check_criteria(self, achievement: Achievement) -> bool:
        """Check if user meets achievement criteria."""
        ctype = achievement.criteria_type
        cvalue = achievement.criteria_value
        
        if ctype == "task_count":
            count = self.db.query(Task).filter(
                Task.user_id == self.user.id,
                Task.status == TaskStatus.COMPLETED
            ).count()
            return count >= cvalue
        
        elif ctype == "habit_count":
            count = self.db.query(Habit).filter(Habit.user_id == self.user.id).count()
            return count >= cvalue
        
        elif ctype == "goal_count":
            count = self.db.query(Goal).filter(Goal.user_id == self.user.id).count()
            return count >= cvalue
        
        elif ctype == "goal_completed":
            count = self.db.query(Goal).filter(
                Goal.user_id == self.user.id,
                Goal.status == GoalStatus.COMPLETED
            ).count()
            return count >= cvalue
        
        elif ctype == "streak_days":
            return self.user.current_streak >= cvalue
        
        elif ctype == "journal_count":
            count = self.db.query(JournalEntry).filter(JournalEntry.user_id == self.user.id).count()
            return count >= cvalue
        
        elif ctype == "level":
            return self.user.level >= cvalue
        
        return False

    # ════════════════════════════════════════════════════════════
    # NOTIFICATIONS
    # ════════════════════════════════════════════════════════════

    def _create_level_up_notification(self, old_level: int, new_level: int):
        notif = Notification(
            user_id=self.user.id,
            title=f"🎉 Level Up! Welcome to Level {new_level}!",
            message=f"You've leveled up from {old_level} to {new_level}! Keep up the amazing work!",
            notification_type=NotificationType.LEVEL_UP,
            priority=NotificationPriority.HIGH,
            icon="🎉",
            color="#fbbf24",
        )
        self.db.add(notif)

    def _create_streak_notification(self, streak_days: int):
        notif = Notification(
            user_id=self.user.id,
            title=f"🔥 {streak_days}-Day Streak!",
            message=f"You've maintained a {streak_days}-day streak. Incredible consistency!",
            notification_type=NotificationType.STREAK,
            priority=NotificationPriority.HIGH,
            icon="🔥",
            color="#ef4444",
        )
        self.db.add(notif)

    def _create_achievement_notification(self, achievement: Achievement):
        notif = Notification(
            user_id=self.user.id,
            title=f"🏆 Achievement Unlocked: {achievement.name}",
            message=f"{achievement.description} (+{achievement.xp_reward} XP)",
            notification_type=NotificationType.ACHIEVEMENT,
            priority=NotificationPriority.HIGH,
            icon=achievement.icon or "🏆",
            color=achievement.badge_color,
        )
        self.db.add(notif)