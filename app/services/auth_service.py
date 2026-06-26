"""
Authentication service layer.

WHY A SERVICE LAYER?
- Separates business logic from HTTP/route logic
- Easier to test (no FastAPI dependency)
- Reusable across multiple endpoints
- Cleaner route handlers
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from datetime import datetime, timezone
from typing import Optional

from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.config import settings


class AuthService:
    """Handles all authentication business logic."""

    def __init__(self, db: Session):
        self.db = db

    # ════════════════════════════════════════════════════════════
    # USER LOOKUP
    # ════════════════════════════════════════════════════════════

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Find user by email (case-insensitive)."""
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Find user by username (case-insensitive)."""
        return self.db.query(User).filter(User.username == username.lower()).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    # ════════════════════════════════════════════════════════════
    # SIGNUP
    # ════════════════════════════════════════════════════════════

    def signup(self, data: SignupRequest) -> User:
        """
        Register a new user.
        
        Raises:
            HTTPException 400 if email or username already exists
        """
        # Check email uniqueness
        if self.get_user_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check username uniqueness
        if self.get_user_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Create new user
        new_user = User(
            email=data.email.lower(),
            username=data.username.lower(),
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            is_active=True,
            is_verified=False,  # Will require email verification later
            xp=0,
            level=1,
            life_score=50,
        )

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        return new_user

    # ════════════════════════════════════════════════════════════
    # LOGIN
    # ════════════════════════════════════════════════════════════

    def authenticate(self, email: str, password: str) -> User:
        """
        Verify credentials and return user.
        
        Raises:
            HTTPException 401 if credentials are invalid
            HTTPException 403 if account is disabled
        """
        user = self.get_user_by_email(email)

        # Use same error message for both cases — prevents email enumeration
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled. Please contact support."
            )

        # Update last_login timestamp
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)

        return user

    # ════════════════════════════════════════════════════════════
    # TOKEN GENERATION
    # ════════════════════════════════════════════════════════════

    def create_tokens(self, user: User) -> dict:
        """
        Generate access + refresh token pair for a user.
        
        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        """
        token_data = {"sub": str(user.id), "email": user.email}

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }