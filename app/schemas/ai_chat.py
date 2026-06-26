"""Pydantic schemas for AI Coach."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.ai_chat import ChatType, MessageRole


# ── REQUEST SCHEMAS ──

class ChatMessageRequest(BaseModel):
    """Single message in a chat conversation."""
    message: str = Field(..., min_length=1, max_length=4000)
    chat_id: Optional[int] = None  # If None, creates new chat
    chat_type: ChatType = ChatType.GENERAL
    include_context: bool = True
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class TaskSuggestionRequest(BaseModel):
    """Request task suggestions."""
    goal_id: Optional[int] = None


class JournalReflectionRequest(BaseModel):
    """Request reflection on a journal entry."""
    entry_id: int


# ── RESPONSE SCHEMAS ──

class AIMessageResponse(BaseModel):
    id: int
    chat_id: int
    role: MessageRole
    content: str
    tokens: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AIChatResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    chat_type: ChatType
    model_name: str
    message_count: int
    total_tokens: int
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    messages: List[AIMessageResponse] = []
    model_config = ConfigDict(from_attributes=True)


class AIChatListItem(BaseModel):
    """Lightweight chat for list view."""
    id: int
    title: Optional[str] = None
    chat_type: ChatType
    message_count: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChatReplyResponse(BaseModel):
    """Response from sending a chat message."""
    chat_id: int
    user_message: AIMessageResponse
    assistant_message: AIMessageResponse


class InsightsResponse(BaseModel):
    insights: str
    generated_at: datetime


class TaskSuggestionResponse(BaseModel):
    suggestions: str
    goal_id: Optional[int] = None
    generated_at: datetime


class JournalReflectionResponse(BaseModel):
    entry_id: int
    reflection: str
    generated_at: datetime


class OllamaStatusResponse(BaseModel):
    status: str
    base_url: Optional[str] = None
    current_model: Optional[str] = None
    available_models: Optional[List[str]] = None
    model_installed: Optional[bool] = None
    error: Optional[str] = None
    message: Optional[str] = None