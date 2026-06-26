"""AI Coach API — chat, insights, suggestions, reflections."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List
from datetime import datetime, timezone
from loguru import logger

from app.database import get_db
from app.models.user import User
from app.models.ai_chat import AIChat, AIMessage, MessageRole, ChatType
from app.schemas.ai_chat import (
    ChatMessageRequest, TaskSuggestionRequest, JournalReflectionRequest,
    AIChatResponse, AIChatListItem, AIMessageResponse, ChatReplyResponse,
    InsightsResponse, TaskSuggestionResponse, JournalReflectionResponse,
    OllamaStatusResponse,
)
from app.core.dependencies import get_current_user
from app.services.ai_service import AIService

router = APIRouter()


# ════════════════════════════════════════════════════════════════
# OLLAMA STATUS CHECK
# ════════════════════════════════════════════════════════════════

@router.get("/status", response_model=OllamaStatusResponse, summary="Check Ollama status")
async def check_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if Ollama is running and the model is installed."""
    service = AIService(db, current_user)
    return await service.check_status()


# ════════════════════════════════════════════════════════════════
# CHAT (non-streaming, full response)
# ════════════════════════════════════════════════════════════════

@router.post("/chat", response_model=ChatReplyResponse, summary="Send a chat message")
async def send_chat(
    data: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to the AI Coach.
    
    - If `chat_id` is provided, continues that conversation
    - Otherwise, starts a new chat
    - User data is automatically included as context
    """
    service = AIService(db, current_user)

    # Get or create chat
    if data.chat_id:
        chat = db.query(AIChat).filter(
            AIChat.id == data.chat_id,
            AIChat.user_id == current_user.id,
        ).first()
        if not chat:
            raise HTTPException(404, "Chat not found")
    else:
        chat = AIChat(
            user_id=current_user.id,
            title=data.message[:60],  # First 60 chars as title
            chat_type=data.chat_type,
            model_name=service.model,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)

    # Save user message
    user_msg = AIMessage(
        chat_id=chat.id,
        role=MessageRole.USER,
        content=data.message,
        tokens=len(data.message.split()),  # Rough estimate
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Build conversation history
    history = db.query(AIMessage).filter(
        AIMessage.chat_id == chat.id,
    ).order_by(AIMessage.id).all()

    messages = [{"role": m.role.value, "content": m.content} for m in history]

    # Call Ollama
    try:
        ai_response = await service.chat(
            messages,
            include_context=data.include_context,
            temperature=data.temperature,
        )
    except Exception as e:
        logger.error(f"AI chat failed: {e}")
        raise HTTPException(503, f"AI service error: {str(e)}")

    # Save assistant message
    assistant_msg = AIMessage(
        chat_id=chat.id,
        role=MessageRole.ASSISTANT,
        content=ai_response,
        tokens=len(ai_response.split()),
        model_name=service.model,
    )
    db.add(assistant_msg)

    # Update chat stats
    chat.message_count += 2
    chat.total_tokens += user_msg.tokens + assistant_msg.tokens
    db.commit()
    db.refresh(assistant_msg)

    return ChatReplyResponse(
        chat_id=chat.id,
        user_message=AIMessageResponse.model_validate(user_msg),
        assistant_message=AIMessageResponse.model_validate(assistant_msg),
    )


# ════════════════════════════════════════════════════════════════
# CHAT (streaming, real-time)
# ════════════════════════════════════════════════════════════════

@router.post("/chat/stream", summary="Stream a chat response (real-time)")
async def stream_chat(
    data: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stream AI response token-by-token for real-time UI updates.
    
    Returns Server-Sent Events (SSE) — each chunk is a piece of the response.
    """
    service = AIService(db, current_user)

    # Get or create chat
    if data.chat_id:
        chat = db.query(AIChat).filter(
            AIChat.id == data.chat_id,
            AIChat.user_id == current_user.id,
        ).first()
        if not chat:
            raise HTTPException(404, "Chat not found")
    else:
        chat = AIChat(
            user_id=current_user.id,
            title=data.message[:60],
            chat_type=data.chat_type,
            model_name=service.model,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)

    # Save user message
    user_msg = AIMessage(
        chat_id=chat.id,
        role=MessageRole.USER,
        content=data.message,
        tokens=len(data.message.split()),
    )
    db.add(user_msg)
    db.commit()

    # Build history
    history = db.query(AIMessage).filter(AIMessage.chat_id == chat.id).order_by(AIMessage.id).all()
    messages = [{"role": m.role.value, "content": m.content} for m in history]

    async def event_generator():
        """Yields SSE events with each chunk."""
        full_response = ""
        async for chunk in service.chat_stream(messages, data.include_context, data.temperature):
            full_response += chunk
            yield f"data: {chunk}\n\n"
        
        # Save full response after streaming completes
        assistant_msg = AIMessage(
            chat_id=chat.id,
            role=MessageRole.ASSISTANT,
            content=full_response,
            tokens=len(full_response.split()),
            model_name=service.model,
        )
        db.add(assistant_msg)
        chat.message_count += 2
        db.commit()
        
        # Signal completion
        yield f"data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ════════════════════════════════════════════════════════════════
# CHAT MANAGEMENT
# ════════════════════════════════════════════════════════════════

@router.get("/chats", response_model=List[AIChatListItem], summary="List all chats")
async def list_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all chat conversations for current user."""
    return db.query(AIChat).filter(
        AIChat.user_id == current_user.id,
        AIChat.is_archived == False,
    ).order_by(desc(AIChat.is_pinned), desc(AIChat.updated_at)).all()


@router.get("/chats/{chat_id}", response_model=AIChatResponse, summary="Get chat with all messages")
async def get_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a chat with full message history."""
    chat = db.query(AIChat).options(joinedload(AIChat.messages)).filter(
        AIChat.id == chat_id,
        AIChat.user_id == current_user.id,
    ).first()
    if not chat:
        raise HTTPException(404, "Chat not found")
    return chat


@router.delete("/chats/{chat_id}", status_code=204, summary="Delete chat")
async def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently delete a chat and all its messages."""
    chat = db.query(AIChat).filter(
        AIChat.id == chat_id,
        AIChat.user_id == current_user.id,
    ).first()
    if not chat:
        raise HTTPException(404, "Chat not found")
    db.delete(chat)
    db.commit()
    return None


@router.post("/chats/{chat_id}/pin", summary="Toggle pin on chat")
async def toggle_pin_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = db.query(AIChat).filter(
        AIChat.id == chat_id,
        AIChat.user_id == current_user.id,
    ).first()
    if not chat:
        raise HTTPException(404, "Chat not found")
    chat.is_pinned = not chat.is_pinned
    db.commit()
    return {"is_pinned": chat.is_pinned}


# ════════════════════════════════════════════════════════════════
# HIGH-LEVEL AI FEATURES
# ════════════════════════════════════════════════════════════════

@router.post("/insights", response_model=InsightsResponse, summary="Generate insights from user data")
async def generate_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI analyzes your tasks, habits, goals, and journal to provide insights.
    
    Returns a personalized analysis with wins, areas to improve, and a suggestion.
    """
    service = AIService(db, current_user)
    try:
        insights = await service.generate_insights()
        return InsightsResponse(
            insights=insights,
            generated_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        raise HTTPException(503, f"AI service error: {str(e)}")


@router.post("/suggest-tasks", response_model=TaskSuggestionResponse, summary="AI suggests tasks based on goals")
async def suggest_tasks(
    data: TaskSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI suggests actionable tasks based on your goals.
    
    Pass a `goal_id` to get suggestions for a specific goal, or leave empty
    for suggestions based on all active goals.
    """
    service = AIService(db, current_user)
    try:
        suggestions = await service.suggest_tasks(data.goal_id)
        return TaskSuggestionResponse(
            suggestions=suggestions,
            goal_id=data.goal_id,
            generated_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        raise HTTPException(503, f"AI service error: {str(e)}")


@router.post("/reflect-journal", response_model=JournalReflectionResponse, summary="AI reflects on a journal entry")
async def reflect_on_journal(
    data: JournalReflectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI reads your journal entry and provides a thoughtful reflection.
    
    Helps you see patterns and insights you might have missed.
    """
    service = AIService(db, current_user)
    try:
        reflection = await service.reflect_on_journal(data.entry_id)
        return JournalReflectionResponse(
            entry_id=data.entry_id,
            reflection=reflection,
            generated_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        raise HTTPException(503, f"AI service error: {str(e)}")


# ════════════════════════════════════════════════════════════════
# CONTEXT PREVIEW (debugging tool)
# ════════════════════════════════════════════════════════════════

@router.get("/context-preview", summary="Preview what data is sent to AI")
async def preview_context(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """See exactly what user data gets passed to the AI as context."""
    service = AIService(db, current_user)
    return {
        "system_prompt": service._get_system_prompt(),
        "user_context": service.build_user_context(),
    }