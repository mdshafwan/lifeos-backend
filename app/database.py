"""
Database connection setup using SQLAlchemy.

WHY SQLAlchemy?
- Industry standard Python ORM
- Handles connection pooling automatically
- Works great with Alembic for migrations
- Type-safe queries with modern SQLAlchemy 2.0 style
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
from loguru import logger

from app.config import settings


# ── Create Engine ────────────────────────────────────────────────
# pool_pre_ping=True — tests connections before using them
# This prevents "connection already closed" errors
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,           # Max 10 connections in pool
    max_overflow=20,        # Allow 20 extra connections under load
    pool_recycle=3600,      # Recycle connections every hour
    echo=settings.DEBUG,    # Log SQL queries in debug mode
)

# ── Session Factory ──────────────────────────────────────────────
# autocommit=False — we control when to commit (safer)
# autoflush=False  — we control when to flush to DB
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ── Base Class ───────────────────────────────────────────────────
# All our SQLAlchemy models will inherit from this
Base = declarative_base()


# ── Dependency ───────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    
    Usage in routes:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    
    The 'yield' makes this a context manager:
    - Opens session before request
    - Closes session after request (even if error occurs)
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()   # Rollback on any error
        raise
    finally:
        db.close()      # Always close the session


# ── Health Check ─────────────────────────────────────────────────
def check_db_connection() -> bool:
    """Test if database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(__import__('sqlalchemy').text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False