# lifeos-backend/app/schemas/otp.py

from pydantic import BaseModel, EmailStr, Field, field_validator


class OTPRequestSchema(BaseModel):
    """Request to start signup — sends OTP to admin."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=200)
    password: str = Field(..., min_length=6, max_length=100)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, _ and -')
        return v
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        return v.strip()


class OTPVerifySchema(BaseModel):
    """Verify OTP and create account."""
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=4, pattern=r'^\d{4}$')


class OTPResendSchema(BaseModel):
    """Resend OTP for pending signup."""
    email: EmailStr


class OTPResponseSchema(BaseModel):
    """Response after OTP is sent/resent."""
    message: str
    email: str
    expires_in_minutes: int
    max_attempts: int