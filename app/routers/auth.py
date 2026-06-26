"""
Authentication router — handles signup, login, logout, refresh, me, OTP.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    RefreshTokenRequest,
    UserResponse,
    TokenResponse,
    AuthResponse,
    MessageResponse,
)
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.core.security import (
    decode_token,
    verify_token_type,
    create_access_token,
    create_refresh_token,
)
from app.config import settings
from loguru import logger

# 🔥 OTP imports
from app.schemas.otp import (
    OTPRequestSchema,
    OTPVerifySchema,
    OTPResendSchema,
    OTPResponseSchema,
)
from app.services.otp_service import otp_service

router = APIRouter()


# ════════════════════════════════════════════════════════════════
# SIGNUP (legacy — direct signup without OTP)
# ════════════════════════════════════════════════════════════════

@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account and returns JWT tokens.",
)
async def signup(
    data: SignupRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **username**: 3-50 chars, alphanumeric + underscores (must be unique)
    - **password**: Min 8 chars, must contain uppercase, lowercase, number
    - **full_name**: Optional display name
    """
    auth_service = AuthService(db)
    user = auth_service.signup(data)
    tokens = auth_service.create_tokens(user)

    logger.info(f"🎉 New user registered: {user.email}")

    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenResponse(**tokens),
    )


# ════════════════════════════════════════════════════════════════
# LOGIN
# ════════════════════════════════════════════════════════════════

@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
    description="Authenticates the user and returns JWT tokens.",
)
async def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return JWT tokens.
    
    - **email**: Your registered email
    - **password**: Your password
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate(data.email, data.password)
    tokens = auth_service.create_tokens(user)

    logger.info(f"🔓 User logged in: {user.email}")

    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenResponse(**tokens),
    )


# ════════════════════════════════════════════════════════════════
# GET CURRENT USER
# ════════════════════════════════════════════════════════════════

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current logged-in user",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Get the currently authenticated user's profile.
    
    Requires `Authorization: Bearer <token>` header.
    """
    return UserResponse.model_validate(current_user)


# ════════════════════════════════════════════════════════════════
# REFRESH TOKEN
# ════════════════════════════════════════════════════════════════

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Use a refresh token to get a new access token.",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Exchange a refresh token for a new access token.
    
    Use this when your access token expires.
    """
    try:
        payload = decode_token(data.refresh_token)

        # Verify it's a refresh token
        if not verify_token_type(payload, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Verify user still exists and is active
        user = db.query(User).filter(User.id == int(user_id_str)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Generate new access token
        new_access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=data.refresh_token,  # Reuse same refresh token
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


# ════════════════════════════════════════════════════════════════
# LOGOUT
# ════════════════════════════════════════════════════════════════

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Logs out the current user (client-side token deletion).",
)
async def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Logout the current user.
    
    **Note**: JWT tokens are stateless. True logout requires the CLIENT to delete
    the token. For server-side blacklisting, we'd need Redis (Phase 9).
    """
    logger.info(f"👋 User logged out: {current_user.email}")
    return MessageResponse(
        message="Successfully logged out. Please discard your tokens.",
        success=True,
    )


# ════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ════════════════════════════════════════════════════════════════

@router.get("/ping", summary="Auth health check")
async def auth_ping():
    """Test that auth router is connected."""
    return {"message": "Auth router is working! 🔐"}


# ════════════════════════════════════════════════════════════════
# 🔥 OTP-BASED SIGNUP (NEW — admin approval required)
# ════════════════════════════════════════════════════════════════

@router.post(
    "/request-otp",
    response_model=OTPResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Request signup OTP — admin gets email",
)
def request_signup_otp(
    payload: OTPRequestSchema,
    db: Session = Depends(get_db),
):
    """
    🔐 Step 1 of signup flow.
    
    - Validates user details
    - Generates 4-digit OTP
    - Emails OTP to admin (mdshafwan14@gmail.com)
    - User must contact admin to get the code
    """
    return otp_service.request_signup_otp(
        db=db,
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        password=payload.password,
    )


# 🔥 FIXED: Returns AuthResponse (which has user + tokens) — matches login/signup
@router.post(
    "/verify-otp",
    response_model=AuthResponse,  # 🔥 CHANGED from TokenResponse to AuthResponse
    status_code=status.HTTP_201_CREATED,
    summary="Verify OTP, create account, and login",
)
def verify_signup_otp(
    payload: OTPVerifySchema,
    db: Session = Depends(get_db),
):
    """
    🔐 Step 2 of signup flow.
    
    - Verifies OTP (max 3 attempts, 5 min expiry)
    - Creates user account
    - Sends welcome email
    - Returns JWT tokens + user (auto-login)
    """
    user = otp_service.verify_signup_otp(
        db=db,
        email=payload.email,
        code=payload.code,
    )

    # 🔥 Generate tokens (same as login/signup pattern)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    refresh_token_str = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )

    logger.info(f"🎉 OTP signup complete: {user.email}")

    # 🔥 Return AuthResponse (same shape as login/signup)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )


@router.post(
    "/resend-otp",
    response_model=OTPResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Resend OTP for pending signup",
)
def resend_signup_otp(
    payload: OTPResendSchema,
    db: Session = Depends(get_db),
):
    """
    🔄 Resend a new OTP if user lost theirs or it expired.
    """
    return otp_service.resend_signup_otp(db=db, email=payload.email)