# lifeos-backend/app/services/otp_service.py

import random
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger
from typing import Optional
from fastapi import HTTPException, status

from app.models.otp import OTPCode
from app.models.user import User
from app.core.security import hash_password
from app.services.email_service import email_service
from app.config import settings


class OTPService:
    """
    🔐 OTP business logic — generate, send, verify.
    """
    
    @staticmethod
    def generate_code() -> str:
        """Generate a random 4-digit OTP."""
        return str(random.randint(1000, 9999))
    
    @staticmethod
    def request_signup_otp(
        db: Session,
        email: str,
        username: str,
        full_name: str,
        password: str,
    ) -> dict:
        """
        🔥 Step 1 of signup: Generate OTP + email admin.
        
        - Validates user doesn't already exist
        - Hashes password
        - Stores OTP record
        - Emails OTP to admin
        """
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This username is already taken",
                )
        
        # Invalidate any existing OTPs for this email
        db.query(OTPCode).filter(
            OTPCode.email == email,
            OTPCode.purpose == "signup",
            OTPCode.used == False,
        ).update({"used": True})
        
        # Generate new OTP
        code = OTPService.generate_code()
        hashed_pw = hash_password(password)
        
        otp = OTPCode(
            email=email,
            username=username,
            full_name=full_name,
            password_hash=hashed_pw,
            code=code,
            purpose="signup",
            expires_at=OTPCode.generate_expiry(),
            max_attempts=settings.OTP_MAX_ATTEMPTS,
        )
        
        db.add(otp)
        db.commit()
        db.refresh(otp)
        
        # Send email to admin
        email_sent = email_service.send_otp_to_admin(
            user_email=email,
            username=username,
            full_name=full_name,
            otp_code=code,
        )
        
        if not email_sent:
            # Rollback — if email fails, OTP is useless
            db.delete(otp)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to send OTP email. Please try again later.",
            )
        
        logger.info(f"🔐 OTP generated for signup: {email} | Code: {code}")
        
        return {
            "message": "OTP sent to admin for approval. Contact admin to receive your code.",
            "email": email,
            "expires_in_minutes": settings.OTP_EXPIRY_MINUTES,
            "max_attempts": settings.OTP_MAX_ATTEMPTS,
        }
    
    @staticmethod
    def verify_signup_otp(
        db: Session,
        email: str,
        code: str,
    ) -> User:
        """
        🔥 Step 2 of signup: Verify OTP + create user.
        """
        # Find most recent valid OTP for this email
        otp = db.query(OTPCode).filter(
            OTPCode.email == email,
            OTPCode.purpose == "signup",
            OTPCode.used == False,
        ).order_by(desc(OTPCode.created_at)).first()
        
        if not otp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No OTP request found for this email. Please request a new OTP.",
            )
        
        # Check if blocked
        if otp.blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Too many failed attempts. Please request a new OTP.",
            )
        
        # Check if expired
        if otp.is_expired():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="OTP has expired. Please request a new one.",
            )
        
        # Increment attempts
        otp.attempts += 1
        
        # Verify code
        if otp.code != code:
            attempts_left = otp.attempts_remaining()
            
            if attempts_left <= 0:
                otp.blocked = True
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Too many failed attempts. Please request a new OTP.",
                )
            
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid OTP. {attempts_left} attempt(s) remaining.",
            )
        
        # ✅ OTP is valid — create user
        otp.used = True
        
        new_user = User(
            email=otp.email,
            username=otp.username,
            full_name=otp.full_name,
            password_hash=otp.password_hash,  # Already hashed
            is_active=True,
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"✅ User created via OTP: {new_user.email} (ID: {new_user.id})")
        
        # Send welcome email (async, don't block on failure)
        try:
            email_service.send_welcome_email(
                user_email=new_user.email,
                full_name=new_user.full_name,
                username=new_user.username,
            )
        except Exception as e:
            logger.warning(f"⚠️ Welcome email failed (non-critical): {e}")
        
        return new_user
    
    @staticmethod
    def resend_signup_otp(db: Session, email: str) -> dict:
        """
        🔄 Resend OTP — generates a NEW code for the same pending signup.
        """
        # Find most recent OTP for this email (used or not)
        last_otp = db.query(OTPCode).filter(
            OTPCode.email == email,
            OTPCode.purpose == "signup",
        ).order_by(desc(OTPCode.created_at)).first()
        
        if not last_otp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pending signup found for this email. Please start signup again.",
            )
        
        # If user has already been created, don't resend
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists. Please login.",
            )
        
        # Invalidate the old OTP
        last_otp.used = True
        
        # Generate new OTP with same user details
        new_code = OTPService.generate_code()
        new_otp = OTPCode(
            email=last_otp.email,
            username=last_otp.username,
            full_name=last_otp.full_name,
            password_hash=last_otp.password_hash,
            code=new_code,
            purpose="signup",
            expires_at=OTPCode.generate_expiry(),
            max_attempts=settings.OTP_MAX_ATTEMPTS,
        )
        
        db.add(new_otp)
        db.commit()
        db.refresh(new_otp)
        
        # Email new OTP to admin
        email_sent = email_service.send_otp_to_admin(
            user_email=last_otp.email,
            username=last_otp.username,
            full_name=last_otp.full_name,
            otp_code=new_code,
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to send OTP email. Please try again later.",
            )
        
        logger.info(f"🔄 OTP resent for signup: {email} | New code: {new_code}")
        
        return {
            "message": "New OTP sent to admin for approval.",
            "email": email,
            "expires_in_minutes": settings.OTP_EXPIRY_MINUTES,
            "max_attempts": settings.OTP_MAX_ATTEMPTS,
        }


# Singleton
otp_service = OTPService()