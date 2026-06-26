"""
Pydantic schemas for authentication endpoints.

WHY SEPARATE SCHEMAS?
- Request schemas: Validate INCOMING data from client
- Response schemas: Define OUTGOING data structure
- Internal schemas: Used between layers
- Never expose password hashes or sensitive data!
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime, date
import re


# ════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS (incoming data)
# ════════════════════════════════════════════════════════════════

class SignupRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="Valid email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 chars)")
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 chars)")
    full_name: Optional[str] = Field(None, max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Username must be alphanumeric + underscores only."""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v.lower()  # Always lowercase for consistency

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce strong password policy."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john@example.com",
                "username": "johndoe",
                "password": "SecurePass123",
                "full_name": "John Doe"
            }
        }
    }


class LoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "test@lifeos.com",
                "password": "password123"
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


# ════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS (outgoing data)
# ════════════════════════════════════════════════════════════════

class UserResponse(BaseModel):
    """User data returned to client (NO password hash!)."""
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    timezone: str
    is_active: bool
    is_verified: bool
    xp: int
    level: int
    life_score: int
    current_streak: int
    longest_streak: int
    last_active_date: Optional[date] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True  # Allow loading from SQLAlchemy models
    }


class TokenResponse(BaseModel):
    """JWT tokens returned on login/signup."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiration


class AuthResponse(BaseModel):
    """Complete auth response with user + tokens."""
    user: UserResponse
    tokens: TokenResponse


class MessageResponse(BaseModel):
    """Simple message response (for logout, etc.)."""
    message: str
    success: bool = True