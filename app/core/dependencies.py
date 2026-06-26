"""
FastAPI dependencies — reusable injection points for routes.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.core.security import decode_token, verify_token_type
from app.models.user import User


# HTTPBearer extracts "Bearer <token>" from Authorization header
security = HTTPBearer(auto_error=True)


# ════════════════════════════════════════════════════════════════
# GET CURRENT USER (PROTECTED ROUTES)
# ════════════════════════════════════════════════════════════════

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the current user from JWT token.
    
    Use this on any endpoint that requires authentication:
    
        @router.get("/me")
        def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    
    Raises:
        401 if token is invalid/expired
        404 if user no longer exists
        403 if account is disabled
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = decode_token(token)

        # Ensure it's an access token (not a refresh token)
        if not verify_token_type(payload, "access"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        user_id = int(user_id_str)

    except JWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception

    # Fetch user from DB
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    return user


# ════════════════════════════════════════════════════════════════
# ADMIN ONLY ROUTES
# ════════════════════════════════════════════════════════════════

async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensures the current user is an admin.
    
    Use for admin-only endpoints:
    
        @router.delete("/users/{id}")
        def delete_user(admin: User = Depends(get_current_admin)):
            ...
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user