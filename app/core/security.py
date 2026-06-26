"""
Security utilities — JWT tokens & password hashing.

WHY THESE CHOICES?
- bcrypt: Slow hashing (good for passwords, resists brute force)
- JWT: Stateless tokens (no DB lookup needed for every request)
- python-jose: Industry standard JWT library for Python
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings


# ── Password Hashing Context ────────────────────────────────────
# bcrypt is the gold standard for password hashing
# It's intentionally slow (~100ms) to make brute force attacks impractical
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ════════════════════════════════════════════════════════════════
# PASSWORD HASHING
# ════════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Example:
        hashed = hash_password("mypassword123")
        # Returns: $2b$12$KqXxYz...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Returns True if match, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════
# JWT TOKEN GENERATION
# ════════════════════════════════════════════════════════════════

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a short-lived JWT access token.
    
    Args:
        data: Payload to encode (usually {"sub": user_id})
        expires_delta: Custom expiration time
    
    Returns:
        JWT token string
    
    Example:
        token = create_access_token({"sub": "1"})
    """
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a long-lived JWT refresh token.
    
    Refresh tokens last longer (days) and are used to get new access tokens.
    """
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ════════════════════════════════════════════════════════════════
# JWT TOKEN VALIDATION
# ════════════════════════════════════════════════════════════════

def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Raises:
        JWTError if token is invalid or expired
    
    Returns:
        Decoded payload dict
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def verify_token_type(payload: dict, expected_type: str = "access") -> bool:
    """Check if token is of the expected type (access or refresh)."""
    return payload.get("type") == expected_type