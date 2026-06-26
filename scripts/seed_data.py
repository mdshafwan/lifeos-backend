"""
Seed script — populates the database with test data.

Usage:
    python scripts/seed_data.py

Creates a test user:
    Email:    test@lifeos.com
    Password: password123
"""

import sys
import os
from datetime import datetime, date, timedelta
import random

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.habit import Habit, HabitCompletion, HabitFrequency, HabitCategory
from app.models.goal import Goal, Milestone, GoalCategory, GoalStatus, GoalPriority
from app.models.note import Note, NoteColor
from app.models.journal import JournalEntry, MoodLevel
from app.models.health import HealthLog, MetricType
from app.models.finance import FinancialAccount, Transaction, AccountType, TransactionType, TransactionCategory
from app.models.contact import Contact, ContactCategory, RelationshipStrength
from app.models.idea import Idea, IdeaCategory, IdeaStatus
from app.models.achievement import Achievement, AchievementCategory, AchievementRarity
from app.models.calendar_event import CalendarEvent, EventType
from loguru import logger


def seed_database():
    """Main seed function."""
    db = SessionLocal()

    try:
        logger.info("🌱 Starting database seeding...")

        # ════════════════════════════════════════════
        # 1. CREATE TEST USER
        # ════════════════════════════════════════════
        existing_user = db.query(User).filter(User.email == "test@lifeos.com").first()
        if existing_user:
            logger.warning("⚠️  Test user already exists. Deleting and recreating...")
            db.delete(existing_user)
            db.commit()

        user = User(
            email="test@lifeos.com",
            username="testuser",
            password_hash=hash_password("password123"),
            full_name="Test User",
            bio="Building amazing things with LifeOS! 🚀",
            timezone="UTC",
            is_active=True,
            is_verified=True,
            xp=250,
            level=3,
            life_score=75,
            current_streak=7,
            longest_streak=14,
            last_active_date=date.today(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.success(f"✅ Created user: {user.email} (ID: {user.id})")

        # ════════════════════════════════════════════
        # 2. CREATE PROJECTS
        # ════════════════════════════════════════════
        projects_data = [
            {"name": "Build LifeOS App", "color": "#3b82f6", "icon": "🚀", "progress": 60},
            {"name": "Learn Python", "color": "#10b981", "icon": "🐍", "progress": 40},
            {"name": "Get Fit", "color": "#ef4444", "icon": "💪", "progress": 30},
            {"name": "Side Hustle", "color": "#f59e0b", "icon": "💰", "progress": 15},
            {"name": "Read 12 Books", "color": "#8b5cf6", "icon": "📚", "progress": 50},
        ]

        projects = []
        for p in projects_data:
            project = Project(
                user_id=user.id,
                name=p["name"],
                description=f"Working on {p['name']}",
                color=p["color"],
                icon=p["icon"],
                status=ProjectStatus.ACTIVE,
                progress=p["progress"],
                start_date=date.today() - timedelta(days=30),
                due_date=date.today() + timedelta(days=60),
            )
            db.add(project)
            projects.append(project)
        db.commit()
        logger.success(f"✅ Created {len(projects)} projects")

        # ════════════════════════════════════════════
        # 3. CREATE TASKS
        # ════════════════════════════════════════════
        tasks_data = [
            ("Design database schema", TaskPriority.HIGH, TaskStatus.COMPLETED, 0),
            ("Build authentication system", TaskPriority.HIGH, TaskStatus.COMPLETED, 0),
            ("Create user dashboard", TaskPriority.MEDIUM, TaskStatus.IN_PROGRESS, 0),
            ("Setup CI/CD pipeline", TaskPriority.LOW, TaskStatus.TODO, 0),
            ("Write unit tests", TaskPriority.MEDIUM, TaskStatus.TODO, 0),
            ("Complete Python basics course", TaskPriority.HIGH, TaskStatus.COMPLETED, 1),
            ("Build FastAPI tutorial project", TaskPriority.MEDIUM, TaskStatus.IN_PROGRESS, 1),
            ("Learn async/await", TaskPriority.LOW, TaskStatus.TODO, 1),
            ("Morning workout routine", TaskPriority.HIGH, TaskStatus.IN_PROGRESS, 2),
            ("Meal prep for the week", TaskPriority.MEDIUM, TaskStatus.TODO, 2),
            ("Research business idea", TaskPriority.HIGH, TaskStatus.IN_PROGRESS, 3),
            ("Build landing page", TaskPriority.MEDIUM, TaskStatus.TODO, 3),
            ("Read 'Atomic Habits'", TaskPriority.LOW, TaskStatus.COMPLETED, 4),
            ("Read 'Deep Work'", TaskPriority.MEDIUM, TaskStatus.IN_PROGRESS, 4),
            ("Write book summary", TaskPriority.LOW, TaskStatus.TODO, 4),
        ]

        for title, priority, status, proj_idx in tasks_data:
            task = Task(
                user_id=user.id,
                project_id=projects[proj_idx].id,
                title=title,
                description=f"Task description for: {title}",
                priority=priority,
                status=status,
                due_date=datetime.now() + timedelta(days=random.randint(1, 30)),
                tags=["work" if proj_idx == 0 else "personal"],
                completed_at=datetime.now() if status == TaskStatus.COMPLETED else None,
            )
            db.add(task)
        db.commit()
        logger.success(f"✅ Created {len(tasks_data)} tasks")

        # ════════════════════════════════════════════
        # 4. CREATE HABITS
        # ════════════════════════════════════════════
        habits_data = [
            ("Drink 8 glasses of water", HabitCategory.HEALTH, "💧", 8, "glasses"),
            ("Exercise for 30 minutes", HabitCategory.FITNESS, "💪", 30, "minutes"),
            ("Read for 30 minutes", HabitCategory.LEARNING, "📚", 30, "minutes"),
            ("Meditate", HabitCategory.MINDFULNESS, "🧘", 10, "minutes"),
            ("Write in journal", HabitCategory.MINDFULNESS, "📝", 1, "entry"),
        ]

        habits = []
        for name, category, icon, target, unit in habits_data:
            habit = Habit(
                user_id=user.id,
                name=name,
                description=f"Daily habit: {name}",
                icon=icon,
                category=category,
                frequency=HabitFrequency.DAILY,
                target_count=target,
                unit=unit,
                current_streak=random.randint(3, 14),
                longest_streak=random.randint(14, 30),
                total_completions=random.randint(20, 60),
                start_date=date.today() - timedelta(days=30),
            )
            db.add(habit)
            habits.append(habit)
        db.commit()

        # Add completion history for past 7 days
        for habit in habits:
            for days_ago in range(7):
                if random.random() > 0.3:  # 70% completion rate
                    completion = HabitCompletion(
                        habit_id=habit.id,
                        user_id=user.id,
                        completion_date=date.today() - timedelta(days=days_ago),
                        count=habit.target_count,
                    )
                    db.add(completion)
        db.commit()
        logger.success(f"✅ Created {len(habits)} habits with completion history")

        # ════════════════════════════════════════════
        # 5. CREATE GOALS WITH MILESTONES
        # ════════════════════════════════════════════
        goals_data = [
            ("Launch LifeOS v1.0", GoalCategory.CAREER, GoalPriority.CRITICAL, 65),
            ("Lose 10kg by year end", GoalCategory.HEALTH, GoalPriority.HIGH, 40),
            ("Save $10,000", GoalCategory.FINANCE, GoalPriority.HIGH, 25),
        ]

        for title, category, priority, progress in goals_data:
            goal = Goal(
                user_id=user.id,
                title=title,
                description=f"My ambitious goal: {title}",
                why=f"This goal will transform my life by achieving {title}",
                category=category,
                priority=priority,
                status=GoalStatus.IN_PROGRESS,
                progress=progress,
                target_date=date.today() + timedelta(days=90),
                start_date=date.today() - timedelta(days=30),
            )
            db.add(goal)
            db.commit()
            db.refresh(goal)

            # Add 3 milestones per goal
            for i in range(3):
                milestone = Milestone(
                    goal_id=goal.id,
                    title=f"Milestone {i+1} for {title}",
                    target_date=date.today() + timedelta(days=(i+1) * 30),
                    is_completed=(i == 0),
                    order_index=i,
                )
                db.add(milestone)
        db.commit()
        logger.success(f"✅ Created {len(goals_data)} goals with milestones")

        # ════════════════════════════════════════════
        # 6. CREATE NOTES
        # ════════════════════════════════════════════
        notes_data = [
            ("Project Ideas", "1. AI Coach Bot\n2. Habit Tracker\n3. Personal CRM", NoteColor.YELLOW, True),
            ("Meeting Notes - Q1 Planning", "Discussed roadmap for Q1...", NoteColor.BLUE, False),
            ("Books to Read", "- Atomic Habits\n- Deep Work\n- The Pragmatic Programmer", NoteColor.GREEN, True),
            ("Recipe: Healthy Smoothie", "Banana, spinach, almond milk, protein powder", NoteColor.ORANGE, False),
        ]

        for title, content, color, pinned in notes_data:
            note = Note(
                user_id=user.id,
                title=title,
                content=content,
                color=color,
                is_pinned=pinned,
                tags=["personal"],
            )
            db.add(note)
        db.commit()
        logger.success(f"✅ Created {len(notes_data)} notes")

        # ════════════════════════════════════════════
        # 7. CREATE JOURNAL ENTRIES
        # ════════════════════════════════════════════
        for days_ago in range(5):
            entry = JournalEntry(
                user_id=user.id,
                entry_date=date.today() - timedelta(days=days_ago),
                title=f"Journal - {date.today() - timedelta(days=days_ago)}",
                content=f"Today was a productive day. I worked on LifeOS and made great progress!",
                mood=random.choice(list(MoodLevel)),
                mood_score=random.randint(6, 10),
                energy_level=random.randint(6, 10),
                stress_level=random.randint(2, 6),
                gratitude=["family", "health", "good food"],
                intentions=["focus on deep work", "exercise"],
            )
            db.add(entry)
        db.commit()
        logger.success("✅ Created 5 journal entries")

        # ════════════════════════════════════════════
        # 8. CREATE HEALTH LOGS
        # ════════════════════════════════════════════
        for days_ago in range(7):
            log_date = date.today() - timedelta(days=days_ago)
            # Weight
            db.add(HealthLog(user_id=user.id, metric_type=MetricType.WEIGHT,
                            log_date=log_date, value=75.5 + random.uniform(-0.5, 0.5), unit="kg"))
            # Steps
            db.add(HealthLog(user_id=user.id, metric_type=MetricType.STEPS,
                            log_date=log_date, value=random.randint(5000, 12000), unit="steps"))
            # Sleep
            db.add(HealthLog(user_id=user.id, metric_type=MetricType.SLEEP_HOURS,
                            log_date=log_date, value=random.uniform(6, 9), unit="hours"))
            # Water
            db.add(HealthLog(user_id=user.id, metric_type=MetricType.WATER,
                            log_date=log_date, value=random.randint(4, 10), unit="glasses"))
        db.commit()
        logger.success("✅ Created 28 health logs (7 days × 4 metrics)")

        # ════════════════════════════════════════════
        # 9. CREATE FINANCIAL ACCOUNTS & TRANSACTIONS
        # ════════════════════════════════════════════
        checking = FinancialAccount(
            user_id=user.id, name="Main Checking", account_type=AccountType.CHECKING,
            institution="Chase Bank", balance=5234.50, initial_balance=5000,
            currency="USD", color="#3b82f6", icon="🏦"
        )
        savings = FinancialAccount(
            user_id=user.id, name="Emergency Fund", account_type=AccountType.SAVINGS,
            institution="Ally Bank", balance=15750.00, initial_balance=10000,
            currency="USD", color="#10b981", icon="💰"
        )
        db.add_all([checking, savings])
        db.commit()
        db.refresh(checking)
        db.refresh(savings)

        # Sample transactions
        transactions_data = [
            (TransactionType.INCOME, TransactionCategory.SALARY, 5000, "Monthly salary"),
            (TransactionType.EXPENSE, TransactionCategory.GROCERIES, -150, "Whole Foods"),
            (TransactionType.EXPENSE, TransactionCategory.SUBSCRIPTIONS, -15, "Netflix"),
            (TransactionType.EXPENSE, TransactionCategory.FOOD, -45, "Restaurant dinner"),
            (TransactionType.EXPENSE, TransactionCategory.TRANSPORTATION, -60, "Gas"),
            (TransactionType.INCOME, TransactionCategory.FREELANCE, 800, "Side project"),
            (TransactionType.EXPENSE, TransactionCategory.ENTERTAINMENT, -25, "Movie tickets"),
        ]

        for ttype, cat, amount, desc in transactions_data:
            txn = Transaction(
                user_id=user.id,
                account_id=checking.id,
                transaction_type=ttype,
                category=cat,
                amount=abs(amount),
                description=desc,
                transaction_date=date.today() - timedelta(days=random.randint(0, 30)),
            )
            db.add(txn)
        db.commit()
        logger.success(f"✅ Created 2 accounts + {len(transactions_data)} transactions")

        # ════════════════════════════════════════════
        # 10. CREATE CONTACTS
        # ════════════════════════════════════════════
        contacts_data = [
            ("John", "Doe", "john@example.com", ContactCategory.FRIEND),
            ("Jane", "Smith", "jane@example.com", ContactCategory.COLLEAGUE),
            ("Mike", "Johnson", "mike@example.com", ContactCategory.MENTOR),
            ("Sarah", "Williams", "sarah@example.com", ContactCategory.CLIENT),
        ]

        for first, last, email, category in contacts_data:
            contact = Contact(
                user_id=user.id,
                first_name=first,
                last_name=last,
                email=email,
                category=category,
                relationship_strength=RelationshipStrength.STRONG,
                tags=["network"],
            )
            db.add(contact)
        db.commit()
        logger.success(f"✅ Created {len(contacts_data)} contacts")

        # ════════════════════════════════════════════
        # 11. CREATE IDEAS
        # ════════════════════════════════════════════
        ideas_data = [
            ("AI-Powered Habit Coach", IdeaCategory.PRODUCT, 9, 7),
            ("Newsletter on Productivity", IdeaCategory.CONTENT, 7, 4),
            ("YouTube Channel - Coding Tutorials", IdeaCategory.CONTENT, 8, 8),
        ]

        for title, category, impact, effort in ideas_data:
            idea = Idea(
                user_id=user.id,
                title=title,
                description=f"Great idea: {title}",
                category=category,
                impact_score=impact,
                effort_score=effort,
                confidence_score=7,
                priority_score=int((impact / effort) * 10),
                status=IdeaStatus.NEW,
            )
            db.add(idea)
        db.commit()
        logger.success(f"✅ Created {len(ideas_data)} ideas")

        # ════════════════════════════════════════════
        # 12. CREATE CALENDAR EVENTS
        # ════════════════════════════════════════════
        events_data = [
            ("Team Standup", EventType.MEETING, 1),
            ("Doctor Appointment", EventType.APPOINTMENT, 3),
            ("Gym Session", EventType.PERSONAL, 0),
            ("Project Deadline", EventType.WORK, 7),
            ("Coffee with Mike", EventType.PERSONAL, 2),
        ]

        for title, etype, days_ahead in events_data:
            event = CalendarEvent(
                user_id=user.id,
                title=title,
                description=f"Calendar event: {title}",
                start_time=datetime.now() + timedelta(days=days_ahead, hours=random.randint(9, 17)),
                end_time=datetime.now() + timedelta(days=days_ahead, hours=random.randint(10, 18)),
                event_type=etype,
            )
            db.add(event)
        db.commit()
        logger.success(f"✅ Created {len(events_data)} calendar events")

        # ════════════════════════════════════════════
        # 13. CREATE SYSTEM ACHIEVEMENTS
        # ════════════════════════════════════════════
        achievements_data = [
            ("first_task", "First Step", "Complete your first task", AchievementCategory.TASKS, AchievementRarity.COMMON, 10, "task_count", 1),
            ("task_master", "Task Master", "Complete 100 tasks", AchievementCategory.TASKS, AchievementRarity.RARE, 100, "task_count", 100),
            ("habit_starter", "Habit Starter", "Create your first habit", AchievementCategory.HABITS, AchievementRarity.COMMON, 10, "habit_count", 1),
            ("week_streak", "Week Warrior", "Maintain a 7-day streak", AchievementCategory.STREAK, AchievementRarity.UNCOMMON, 50, "streak_days", 7),
            ("month_streak", "Monthly Master", "Maintain a 30-day streak", AchievementCategory.STREAK, AchievementRarity.RARE, 200, "streak_days", 30),
            ("goal_setter", "Goal Setter", "Create your first goal", AchievementCategory.GOALS, AchievementRarity.COMMON, 20, "goal_count", 1),
            ("goal_crusher", "Goal Crusher", "Complete 10 goals", AchievementCategory.GOALS, AchievementRarity.EPIC, 500, "goal_completed", 10),
            ("journal_writer", "Journal Writer", "Write 30 journal entries", AchievementCategory.JOURNAL, AchievementRarity.UNCOMMON, 75, "journal_count", 30),
            ("level_10", "Rising Star", "Reach level 10", AchievementCategory.MILESTONE, AchievementRarity.RARE, 100, "level", 10),
            ("legendary", "Legendary", "Reach level 50", AchievementCategory.MILESTONE, AchievementRarity.LEGENDARY, 1000, "level", 50),
        ]

        for code, name, desc, cat, rarity, xp, ctype, cvalue in achievements_data:
            existing = db.query(Achievement).filter(Achievement.code == code).first()
            if not existing:
                ach = Achievement(
                    code=code, name=name, description=desc,
                    category=cat, rarity=rarity, xp_reward=xp,
                    criteria_type=ctype, criteria_value=cvalue,
                )
                db.add(ach)
        db.commit()
        logger.success(f"✅ Created {len(achievements_data)} system achievements")

        # ════════════════════════════════════════════
        # SUMMARY
        # ════════════════════════════════════════════
        logger.info("=" * 60)
        logger.success("🎉 DATABASE SEEDED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"📧 Test User Email:    test@lifeos.com")
        logger.info(f"🔐 Test User Password: password123")
        logger.info(f"👤 User ID:            {user.id}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()