"""
Base model — all other models inherit from this.
Provides id + created_at + updated_at fields automatically.
"""

from sqlalchemy import Column, Integer, DateTime, func
from app.database import Base


class TimestampMixin:
    """Adds created_at + updated_at to any model."""
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    """Abstract base — gives id + timestamps to all models."""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)