"""
AI Chat models:
- AIChat: A conversation thread
- AIMessage: Individual messages within a conversation
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class ChatType(str, enum.Enum):
    GENERAL = "general"
    COACHING = "coaching"
    JOURNAL_REFLECTION = "journal_reflection"
    GOAL_PLANNING = "goal_planning"
    TASK_SUGGESTION = "task_suggestion"
    INSIGHTS = "insights"
    OTHER = "other"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AIChat(BaseModel):
    """A chat session/conversation with AI Coach."""
    __tablename__ = "ai_chats"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    title = Column(String(300), nullable=True)              # Auto-generated from first message
    chat_type = Column(Enum(ChatType), default=ChatType.GENERAL, nullable=False, index=True)

    # ── Context (snapshot of user data at chat time) ──
    context_data = Column(JSON, default=dict, nullable=False)  # {"goals": [...], "tasks": [...]}

    # ── Model Info ────────────────────────────────────
    model_name = Column(String(100), default="llama3", nullable=False)

    # ── Stats ─────────────────────────────────────────
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)

    # ── Flags ─────────────────────────────────────────
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="ai_chats")
    messages = relationship("AIMessage", back_populates="chat", cascade="all, delete-orphan", order_by="AIMessage.id")

    def __repr__(self):
        return f"<AIChat(id={self.id}, type='{self.chat_type}', messages={self.message_count})>"


class AIMessage(BaseModel):
    """Individual message in an AI chat conversation."""
    __tablename__ = "ai_messages"

    chat_id = Column(Integer, ForeignKey("ai_chats.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Message Content ───────────────────────────────
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)

    # ── Metadata ──────────────────────────────────────
    tokens = Column(Integer, default=0, nullable=False)
    model_name = Column(String(100), nullable=True)

    # ── Extra Data ────────────────────────────────────
    extra_data = Column(JSON, default=dict, nullable=False)  # {"function_call": {...}, "sources": [...]}

    # ── Relationships ─────────────────────────────────
    chat = relationship("AIChat", back_populates="messages")

    def __repr__(self):
        return f"<AIMessage(chat_id={self.chat_id}, role='{self.role}')>"