"""
Application configuration using Pydantic Settings.
Reads from .env file automatically.

WHY Pydantic Settings?
- Type validation on your env vars (catches typos early)
- Auto-loads from .env file
- Single source of truth for all config
"""

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
from typing import List, Optional, Union
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ── App ─────────────────────────────────
    APP_NAME: str = "LifeOS Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ── Server ──────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ────────────────────────────
    DATABASE_URL: str

    # ── JWT ─────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated string to list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # ── File Storage ────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    # ── AI Provider ─────────────────────────
    AI_PROVIDER: str = "groq"  # "groq" | "ollama"

    # ── Groq (Production) ───────────────────
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # ── Ollama (Local Dev) ──────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # ── Email ───────────────────────────────
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # ── Gamification XP ─────────────────────
    XP_TASK_COMPLETE: int = 10
    XP_HABIT_COMPLETE: int = 15
    XP_GOAL_COMPLETE: int = 100
    XP_JOURNAL_ENTRY: int = 5
    XP_LOGIN_STREAK: int = 20


    RESEND_API_KEY: str
    ADMIN_EMAIL: str = "mdshafwan14@gmail.com"
    EMAIL_FROM: str = "LifeOS <onboarding@resend.dev>"
    OTP_EXPIRY_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    

    

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ── Singleton pattern ────────────────────────────────────────────
# lru_cache means this function is only called ONCE — same Settings
# object is reused everywhere. Very efficient!
@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Convenience instance — import this everywhere
settings = get_settings()