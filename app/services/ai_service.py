"""
AI Coach service — supports Groq (cloud) and Ollama (local).

Switch providers by setting AI_PROVIDER in .env:
- "groq"   → Cloud API (free, fast, works on Render)
- "ollama" → Local LLM (offline, private)
"""

import httpx
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, timedelta
from loguru import logger

from app.config import settings
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.habit import Habit
from app.models.goal import Goal, GoalStatus
from app.models.journal import JournalEntry


class AIService:
    """Wrapper around AI providers (Groq or Ollama)."""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.provider = settings.AI_PROVIDER.lower()
        
        if self.provider == "groq":
            self.model = settings.GROQ_MODEL
            self.api_key = settings.GROQ_API_KEY
            if not self.api_key:
                logger.warning("⚠️ GROQ_API_KEY not set! AI features will fail.")
        elif self.provider == "ollama":
            self.model = settings.OLLAMA_MODEL
            self.base_url = settings.OLLAMA_BASE_URL
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")

    # ════════════════════════════════════════════════════════════
    # SYSTEM PROMPT
    # ════════════════════════════════════════════════════════════

    def _get_system_prompt(self) -> str:
        return f"""You are a personal life coach AI for LifeOS, helping {self.user.full_name or self.user.username} achieve their goals.

Your style:
- Warm, encouraging, and direct
- Use the user's name occasionally to personalize
- Give actionable advice, not generic platitudes
- Reference their actual data (tasks, goals, habits) when relevant
- Keep responses concise (2-4 paragraphs max unless asked)
- Use markdown for formatting (lists, bold for emphasis)
- Ask clarifying questions when needed
- Celebrate wins, however small
- Be honest about challenges without being negative

You are NOT a therapist or medical professional."""

    # ════════════════════════════════════════════════════════════
    # CONTEXT BUILDER
    # ════════════════════════════════════════════════════════════

    def build_user_context(self) -> str:
        context_parts = [
            f"## User Profile",
            f"- Name: {self.user.full_name or self.user.username}",
            f"- Level: {self.user.level} ({self.user.xp} XP)",
            f"- Life Score: {self.user.life_score}/100",
            f"- Current Streak: {self.user.current_streak} days",
        ]

        active_goals = self.db.query(Goal).filter(
            Goal.user_id == self.user.id,
            Goal.status == GoalStatus.IN_PROGRESS,
        ).limit(5).all()
        if active_goals:
            context_parts.append("\n## Active Goals")
            for g in active_goals:
                context_parts.append(f"- {g.title} ({g.progress}% complete, category: {g.category.value})")

        recent_tasks = self.db.query(Task).filter(
            Task.user_id == self.user.id,
        ).order_by(desc(Task.created_at)).limit(10).all()
        if recent_tasks:
            todo = [t for t in recent_tasks if t.status == TaskStatus.TODO]
            in_progress = [t for t in recent_tasks if t.status == TaskStatus.IN_PROGRESS]
            completed = [t for t in recent_tasks if t.status == TaskStatus.COMPLETED]
            context_parts.append(f"\n## Recent Tasks ({len(todo)} todo, {len(in_progress)} in progress, {len(completed)} completed)")
            for t in (todo + in_progress)[:5]:
                context_parts.append(f"- [{t.status.value}] {t.title} (priority: {t.priority.value})")

        habits = self.db.query(Habit).filter(
            Habit.user_id == self.user.id,
            Habit.is_active == True,
        ).limit(5).all()
        if habits:
            context_parts.append("\n## Habits")
            for h in habits:
                context_parts.append(f"- {h.name} (current streak: {h.current_streak} days)")

        recent_journal = self.db.query(JournalEntry).filter(
            JournalEntry.user_id == self.user.id,
        ).order_by(desc(JournalEntry.entry_date)).limit(3).all()
        if recent_journal:
            context_parts.append("\n## Recent Mood")
            for j in recent_journal:
                mood = j.mood.value if j.mood else "not recorded"
                context_parts.append(f"- {j.entry_date}: mood was {mood}")

        return "\n".join(context_parts)

    # ════════════════════════════════════════════════════════════
    # PROVIDER-AGNOSTIC CHAT METHODS
    # ════════════════════════════════════════════════════════════

    async def chat(
        self,
        messages: List[Dict[str, str]],
        include_context: bool = True,
        temperature: float = 0.7,
    ) -> str:
        """Send chat messages and get full response."""
        system_prompt = self._get_system_prompt()
        if include_context:
            system_prompt += f"\n\n## Current User Data\n{self.build_user_context()}"

        formatted_messages = [{"role": "system", "content": system_prompt}] + messages

        if self.provider == "groq":
            return await self._groq_chat(formatted_messages, temperature)
        else:
            return await self._ollama_chat(formatted_messages, temperature)

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        include_context: bool = True,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response chunk-by-chunk."""
        system_prompt = self._get_system_prompt()
        if include_context:
            system_prompt += f"\n\n## Current User Data\n{self.build_user_context()}"

        formatted_messages = [{"role": "system", "content": system_prompt}] + messages

        if self.provider == "groq":
            async for chunk in self._groq_stream(formatted_messages, temperature):
                yield chunk
        else:
            async for chunk in self._ollama_stream(formatted_messages, temperature):
                yield chunk

    # ════════════════════════════════════════════════════════════
    # GROQ IMPLEMENTATION
    # ════════════════════════════════════════════════════════════

    async def _groq_chat(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Call Groq API for full response."""
        if not self.api_key:
            raise Exception("GROQ_API_KEY not configured")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            logger.error(f"Groq API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"AI service error: {str(e)}")

    async def _groq_stream(self, messages: List[Dict[str, str]], temperature: float):
        """Stream Groq response chunks."""
        if not self.api_key:
            raise Exception("GROQ_API_KEY not configured")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", "https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data["choices"][0]["delta"]
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except httpx.HTTPError as e:
            logger.error(f"Groq stream error: {e}")
            yield f"\n\n[Error: {str(e)}]"

    # ════════════════════════════════════════════════════════════
    # OLLAMA IMPLEMENTATION
    # ════════════════════════════════════════════════════════════

    async def _ollama_chat(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Call Ollama for full response."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                return response.json().get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            logger.error(f"Ollama error: {e}")
            raise Exception(f"AI service unavailable: {str(e)}")

    async def _ollama_stream(self, messages: List[Dict[str, str]], temperature: float):
        """Stream Ollama response chunks."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature},
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                content = data.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except httpx.HTTPError as e:
            logger.error(f"Ollama stream error: {e}")
            yield f"\n\n[Error: {str(e)}]"

    # ════════════════════════════════════════════════════════════
    # HIGH-LEVEL FEATURES
    # ════════════════════════════════════════════════════════════

    async def generate_insights(self) -> str:
        prompt = """Based on my current data, give me a brief but insightful analysis:

1. **What's going well** (1-2 specific wins to celebrate)
2. **What needs attention** (1-2 areas where I'm falling behind)
3. **One actionable suggestion** for the next 7 days

Keep it under 200 words, friendly tone."""
        return await self.chat([{"role": "user", "content": prompt}])

    async def suggest_tasks(self, goal_id: Optional[int] = None) -> str:
        if goal_id:
            goal = self.db.query(Goal).filter(
                Goal.id == goal_id, Goal.user_id == self.user.id
            ).first()
            if not goal:
                return "Goal not found."
            prompt = f"""Based on my goal "{goal.title}" (currently {goal.progress}% complete), suggest 5 specific, actionable tasks I should add to my list.

For each task include:
- Clear action verb
- Estimated time
- Priority (low/medium/high)

Format as a numbered list."""
        else:
            prompt = """Based on my active goals, suggest 5 high-impact tasks I should focus on this week. Each should be specific and actionable."""
        return await self.chat([{"role": "user", "content": prompt}])

    async def reflect_on_journal(self, entry_id: int) -> str:
        entry = self.db.query(JournalEntry).filter(
            JournalEntry.id == entry_id, JournalEntry.user_id == self.user.id
        ).first()
        if not entry:
            return "Journal entry not found."
        prompt = f"""I wrote this journal entry on {entry.entry_date}:

"{entry.content}"

My mood was: {entry.mood.value if entry.mood else "not recorded"}

Please reflect on this with me. Help me see patterns or insights I might have missed. Be supportive but honest. Keep response under 200 words."""
        return await self.chat([{"role": "user", "content": prompt}], include_context=False)

    async def check_status(self) -> Dict[str, Any]:
        """Check if AI service is reachable."""
        if self.provider == "groq":
            return {
                "status": "healthy" if self.api_key else "unconfigured",
                "provider": "groq",
                "model": self.model,
                "api_key_set": bool(self.api_key),
                "message": "Groq API ready" if self.api_key else "Set GROQ_API_KEY in .env",
            }
        else:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.base_url}/api/tags")
                    response.raise_for_status()
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {
                        "status": "healthy",
                        "provider": "ollama",
                        "base_url": self.base_url,
                        "model": self.model,
                        "available_models": models,
                        "model_installed": self.model in models,
                    }
            except Exception as e:
                return {
                    "status": "unavailable",
                    "provider": "ollama",
                    "error": str(e),
                    "message": "Make sure Ollama is running",
                }