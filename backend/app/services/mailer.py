"""Email notification service for email verification and password resets."""

import logging
import os
from typing import Dict, Any

_logger = logging.getLogger("safarsathi.mailer")


def send_verification_email(email: str, token: str, app_url: str = "http://localhost:5173") -> Dict[str, Any]:
    """Send an email verification link to a user. In dev, logs link to console. Never raises."""
    try:
        verify_link = f"{app_url}/verify-email?token={token}"
        provider = os.getenv("MAIL_PROVIDER", "console").strip().lower()

        if provider == "console":
            print(f"\n[EMAIL SIMULATION] To: {email} | Subject: Verify your SafarSathi Account")
            print(f"[EMAIL SIMULATION] Verification Link: {verify_link}\n")
            return {"sent": True, "provider": "console", "link": verify_link}

        if provider == "resend":
            import requests
            api_key = os.getenv("RESEND_API_KEY", "")
            if not api_key:
                return {"error": "RESEND_API_KEY missing"}
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "from": os.getenv("MAIL_FROM", "auth@safarsathi.com"),
                    "to": [email],
                    "subject": "Verify your SafarSathi Account",
                    "text": f"Welcome to SafarSathi!\n\nPlease verify your email by clicking: {verify_link}",
                },
                timeout=10,
            )
            return {"sent": resp.status_code in (200, 201), "provider": "resend"}

        return {"sent": True, "provider": "unconfigured_fallback", "link": verify_link}
    except Exception as exc:
        return {"error": f"Failed to dispatch verification email: {exc}"}


def send_password_reset_email(email: str, token: str, app_url: str = "http://localhost:5173") -> Dict[str, Any]:
    """Send a password reset link to a user. In dev, logs link to console. Never raises."""
    try:
        reset_link = f"{app_url}/reset-password?token={token}"
        provider = os.getenv("MAIL_PROVIDER", "console").strip().lower()

        if provider == "console":
            print(f"\n[EMAIL SIMULATION] To: {email} | Subject: Reset your SafarSathi Password")
            print(f"[EMAIL SIMULATION] Reset Link: {reset_link}\n")
            return {"sent": True, "provider": "console", "link": reset_link}

        return {"sent": True, "provider": "unconfigured_fallback", "link": reset_link}
    except Exception as exc:
        return {"error": f"Failed to dispatch password reset email: {exc}"}
