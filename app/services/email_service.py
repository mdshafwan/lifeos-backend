# lifeos-backend/app/services/email_service.py

import resend
from loguru import logger
from app.config import settings
from datetime import datetime

# Initialize Resend
resend.api_key = settings.RESEND_API_KEY


class EmailService:
    """
    📧 Email service using Resend API.
    
    Sends:
      - OTP codes to admin (for signup approval)
      - Welcome emails to new users
    """
    
    @staticmethod
    def send_otp_to_admin(
        user_email: str,
        username: str,
        full_name: str,
        otp_code: str,
    ) -> bool:
        """
        Send OTP to admin email for signup approval.
        Admin shares the code with the user manually.
        """
        try:
            timestamp = datetime.utcnow().strftime("%b %d, %Y at %I:%M %p UTC")
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>LifeOS — New Account Request</title>
</head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#080b14;">
  <div style="max-width:600px;margin:40px auto;background:#0d1117;border-radius:16px;overflow:hidden;border:1px solid #1f2937;">
    
    <!-- Header -->
    <div style="padding:32px 32px 16px;text-align:center;background:linear-gradient(135deg,#6366f1,#8b5cf6);">
      <h1 style="margin:0;color:#fff;font-size:24px;font-weight:800;letter-spacing:-0.5px;">
        🔐 LifeOS
      </h1>
      <p style="margin:8px 0 0;color:rgba(255,255,255,0.85);font-size:14px;font-weight:500;">
        New Account Request
      </p>
    </div>
    
    <!-- Body -->
    <div style="padding:32px;">
      <p style="margin:0 0 24px;color:#cbd5e1;font-size:15px;line-height:1.6;">
        Someone is trying to create an account on your LifeOS app. Review the details below:
      </p>
      
      <!-- User details card -->
      <div style="background:#111827;border:1px solid #1f2937;border-radius:12px;padding:20px;margin-bottom:24px;">
        <table style="width:100%;border-collapse:collapse;">
          <tr>
            <td style="padding:6px 0;color:#64748b;font-size:13px;font-weight:600;width:120px;">👤 Name</td>
            <td style="padding:6px 0;color:#f1f5f9;font-size:14px;font-weight:600;">{full_name}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#64748b;font-size:13px;font-weight:600;">📧 Email</td>
            <td style="padding:6px 0;color:#f1f5f9;font-size:14px;font-weight:600;">{user_email}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#64748b;font-size:13px;font-weight:600;">🆔 Username</td>
            <td style="padding:6px 0;color:#f1f5f9;font-size:14px;font-weight:600;">@{username}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#64748b;font-size:13px;font-weight:600;">🕐 Time</td>
            <td style="padding:6px 0;color:#94a3b8;font-size:13px;">{timestamp}</td>
          </tr>
        </table>
      </div>
      
      <!-- OTP Code Box -->
      <div style="background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(139,92,246,0.08));border:2px solid rgba(99,102,241,0.4);border-radius:14px;padding:28px;text-align:center;margin-bottom:24px;">
        <div style="font-size:11px;font-weight:800;color:#a5b4fc;letter-spacing:2px;margin-bottom:12px;">
          OTP CODE
        </div>
        <div style="font-size:48px;font-weight:900;color:#f1f5f9;letter-spacing:12px;font-family:'Courier New',monospace;margin:8px 0;">
          {otp_code}
        </div>
        <div style="font-size:12px;color:#94a3b8;margin-top:12px;font-weight:500;">
          ⏰ Expires in {settings.OTP_EXPIRY_MINUTES} minutes
        </div>
      </div>
      
      <!-- Instructions -->
      <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);border-radius:10px;padding:16px;margin-bottom:16px;">
        <p style="margin:0;color:#6ee7b7;font-size:13px;line-height:1.6;">
          <strong>✅ To approve:</strong> Share this code with the user.
        </p>
      </div>
      
      <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);border-radius:10px;padding:16px;">
        <p style="margin:0;color:#fca5a5;font-size:13px;line-height:1.6;">
          <strong>❌ To deny:</strong> Just ignore this email. The OTP will expire automatically.
        </p>
      </div>
    </div>
    
    <!-- Footer -->
    <div style="padding:20px 32px;background:#0a0d15;border-top:1px solid #1f2937;text-align:center;">
      <p style="margin:0;color:#475569;font-size:11px;font-weight:500;">
        LifeOS — Your Personal Life Operating System
      </p>
    </div>
    
  </div>
</body>
</html>
"""
            
            response = resend.Emails.send({
                "from": settings.EMAIL_FROM,
                "to": settings.ADMIN_EMAIL,
                "subject": f"🔐 LifeOS — New Account Request from {full_name} (OTP: {otp_code})",
                "html": html_content,
            })
            
            logger.info(f"✅ OTP email sent to admin for {user_email} | Resend ID: {response.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send OTP email: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(user_email: str, full_name: str, username: str) -> bool:
        """Send a welcome email to the user after successful signup."""
        try:
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Welcome to LifeOS!</title>
</head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#080b14;">
  <div style="max-width:600px;margin:40px auto;background:#0d1117;border-radius:16px;overflow:hidden;border:1px solid #1f2937;">
    
    <div style="padding:40px 32px;text-align:center;background:linear-gradient(135deg,#6366f1,#8b5cf6,#ec4899);">
      <div style="font-size:48px;margin-bottom:12px;">🎉</div>
      <h1 style="margin:0;color:#fff;font-size:28px;font-weight:800;letter-spacing:-0.5px;">
        Welcome to LifeOS!
      </h1>
      <p style="margin:8px 0 0;color:rgba(255,255,255,0.9);font-size:15px;font-weight:500;">
        Your journey starts now, {full_name.split()[0]} 🚀
      </p>
    </div>
    
    <div style="padding:32px;">
      <p style="margin:0 0 16px;color:#f1f5f9;font-size:16px;line-height:1.6;font-weight:600;">
        Hey {full_name}! 👋
      </p>
      <p style="margin:0 0 24px;color:#cbd5e1;font-size:14px;line-height:1.7;">
        Your account <strong style="color:#a5b4fc;">@{username}</strong> has been successfully created. 
        You now have access to your personal life operating system with 20+ powerful modules.
      </p>
      
      <div style="background:#111827;border:1px solid #1f2937;border-radius:12px;padding:20px;margin-bottom:24px;">
        <div style="font-size:11px;font-weight:800;color:#a5b4fc;letter-spacing:1.5px;margin-bottom:14px;text-transform:uppercase;">
          🎯 What's Inside
        </div>
        <div style="color:#cbd5e1;font-size:13px;line-height:2;">
          ✅ Task & Project Management<br>
          🔥 Habit Tracker with Streaks<br>
          🎯 Goal Setting + Milestones<br>
          📔 Journal & Notes<br>
          🤖 AI Life Coach (8 Personalities!)<br>
          💰 Finance & Health Tracking<br>
          📊 Personal Analytics<br>
          🏆 Gamification (XP, Levels, Achievements)
        </div>
      </div>
      
      <div style="text-align:center;margin:32px 0;">
        <a href="http://localhost:5173/login" style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;text-decoration:none;border-radius:10px;font-size:14px;font-weight:700;letter-spacing:0.3px;">
          🚀 Open LifeOS
        </a>
      </div>
      
      <p style="margin:24px 0 0;color:#64748b;font-size:12px;line-height:1.6;text-align:center;">
        Need help? Just reply to this email.
      </p>
    </div>
    
    <div style="padding:20px 32px;background:#0a0d15;border-top:1px solid #1f2937;text-align:center;">
      <p style="margin:0;color:#475569;font-size:11px;font-weight:500;">
        LifeOS — Your Life, Optimized ∞
      </p>
    </div>
    
  </div>
</body>
</html>
"""
            
            response = resend.Emails.send({
                "from": settings.EMAIL_FROM,
                "to": user_email,
                "subject": f"🎉 Welcome to LifeOS, {full_name.split()[0]}!",
                "html": html_content,
            })
            
            logger.info(f"✅ Welcome email sent to {user_email} | Resend ID: {response.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send welcome email: {e}")
            return False


# Singleton instance
email_service = EmailService()