"""
Alembic environment configuration.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import settings and Base
from app.config import settings
from app.database import Base

# Import ALL models so Alembic detects them
from app.models.user import User  # noqa
from app.models.project import Project  # noqa
from app.models.task import Task  # noqa
from app.models.habit import Habit, HabitCompletion  # noqa
from app.models.goal import Goal, Milestone  # noqa
from app.models.calendar_event import CalendarEvent  # noqa
# ── Knowledge Models (Phase 2D) ──
from app.models.note import Note  # noqa
from app.models.journal import JournalEntry  # noqa
from app.models.wiki import Wiki  # noqa
from app.models.learning import Learning  # noqa
from app.models.idea import Idea  # noqa
# ── Life Models (Phase 2E) ──
from app.models.health import HealthLog  # noqa
from app.models.finance import FinancialAccount, Transaction  # noqa
from app.models.vision_board import VisionBoard  # noqa
# ── Business Models (Phase 2F) ──
from app.models.business import Business  # noqa
from app.models.contact import Contact  # noqa
from app.models.document import Document  # noqa
# ── Gamification Models (Phase 2G) ──
from app.models.achievement import Achievement, UserAchievement  # noqa
from app.models.notification import Notification  # noqa
from app.models.ai_chat import AIChat, AIMessage  # noqa


# Alembic config object
config = context.config

# alembic/env.py line 49
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))
# Setup loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()