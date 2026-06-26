# lifeos-backend/app/models/otp.py

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Index
from datetime import datetime, timedelta
from app.models.base import BaseModel
from app.config import settings


class OTPCode(BaseModel):
    """
    🔐 One-Time Password for account verification.
    
    Flow:
      1. User requests signup → OTP generated + emailed to admin
      2. User enters OTP from admin → verified
      3. Account created
    """
    __tablename__ = "otp_codes"
    
    # User-provided data (stored until verification)
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    password_hash = Column(String(255), nullable=False)  # Pre-hashed password
    
    # OTP data
    code = Column(String(4), nullable=False)  # 4-digit code
    purpose = Column(String(50), default="signup")  # signup, password_reset, etc.
    
    # Tracking
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    used = Column(Boolean, default=False)
    blocked = Column(Boolean, default=False)  # True after max_attempts exceeded
    
    # Composite index for fast lookups
    __table_args__ = (
        Index('ix_otp_email_purpose', 'email', 'purpose'),
    )
    
    def is_expired(self) -> bool:
        """Check if OTP has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if OTP is still valid (not used, not blocked, not expired)."""
        return not self.used and not self.blocked and not self.is_expired()
    
    def attempts_remaining(self) -> int:
        """How many more attempts the user has."""
        return max(0, self.max_attempts - self.attempts)
    
    @classmethod
    def generate_expiry(cls) -> datetime:
        """Generate expiry timestamp based on settings."""
        return datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
    def __repr__(self):
        return f"<OTPCode email={self.email} code={self.code} used={self.used}>"