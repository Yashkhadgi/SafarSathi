"""Authentication and Account Management API endpoints."""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.rate_limit import check_rate_limit, clear_failed_attempts, record_failed_attempt
from backend.app.core.security import (
    create_access_token,
    generate_csrf_token,
    generate_random_token,
    hash_password,
    hash_token,
    verify_password,
)
from backend.app.db.models.user import AuthSession, EmailToken, LoginEvent, User
from backend.app.repositories.chat_repo import list_conversations
from backend.app.repositories.profile_repo import get_or_create_profile, list_trusted_contacts
from backend.app.repositories.trip_repo import list_trips
from backend.app.repositories.user_repo import (
    create_auth_session,
    create_user,
    delete_user,
    get_active_auth_session,
    get_user_by_email,
    get_user_by_id,
    record_login_event,
    revoke_all_user_sessions,
    revoke_auth_session,
)
from backend.app.services.mailer import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


# --- Schemas ---

class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    password: str


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set hardened HTTP-only, SameSite cookies for access and refresh tokens."""
    # 15 min access token
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=15 * 60,
        httponly=True,
        secure=False,  # Set to True in HTTPS production
        samesite="lax",
        path="/",
    )
    # 30 day refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=30 * 24 * 60 * 60,
        httponly=True,
        secure=False,  # Set to True in HTTPS production
        samesite="lax",
        path="/api/v1/auth",
    )
    # Anti-CSRF double submit token
    response.set_cookie(
        key="csrf_token",
        value=generate_csrf_token(),
        max_age=30 * 24 * 60 * 60,
        httponly=False,  # Accessible by frontend to pass in X-CSRF-Token header
        secure=False,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response):
    """Clear authentication cookies upon logout."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    response.delete_cookie(key="csrf_token", path="/")


# --- Endpoints ---

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(req: SignupRequest, request: Request, db: Session = Depends(get_db)):
    """Register a new user account with argon2id/PBKDF2 password hashing."""
    ip = request.client.host if request.client else "unknown"
    allowed, retry_after = check_rate_limit(f"signup_{ip}", max_requests=5, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many signup attempts. Please try again in {retry_after} seconds.",
        )

    email = req.email.strip().casefold()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid email address.")
    if len(req.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")

    existing = get_user_by_email(db, email)
    if existing:
        # Generic response to prevent user enumeration
        return {"message": "If this email is not registered, a verification link has been sent.", "status": "pending_verification"}

    hashed_pw = hash_password(req.password)
    user = create_user(db, email=email, password_hash=hashed_pw, is_verified=False)
    
    # Generate verification token
    raw_token = generate_random_token()
    token_h = hash_token(raw_token)
    exp = datetime.now(timezone.utc) + timedelta(hours=24)
    
    db_token = EmailToken(
        user_id=user.id,
        token_hash=token_h,
        token_type="verify_email",
        expires_at=exp,
    )
    db.add(db_token)
    db.commit()

    # Send verification link
    send_verification_email(email, raw_token)

    return {"message": "Account created. Please verify your email.", "status": "pending_verification", "user_id": user.id}


@router.post("/verify-email")
def verify_email(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify an email token."""
    token_h = hash_token(req.token.strip())
    now = datetime.now(timezone.utc)
    
    email_token = db.query(EmailToken).filter(
        EmailToken.token_hash == token_h,
        EmailToken.token_type == "verify_email",
        EmailToken.used_at.is_(None),
        EmailToken.expires_at > now,
    ).first()

    if not email_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token.")

    user = get_user_by_id(db, email_token.user_id)
    if user:
        user.is_verified = True
    email_token.used_at = now
    db.commit()

    return {"message": "Email verified successfully. You can now log in.", "verified": True}


@router.post("/login")
def login(req: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    """Authenticate with email and password, setting secure httpOnly cookies."""
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")
    email = req.email.strip().casefold()

    # Check brute force lockout
    allowed, retry_after = check_rate_limit(f"login_{ip}", max_requests=10, window_seconds=60)
    if not allowed:
        record_login_event(db, email, ip, False, user_agent=user_agent, failure_reason="rate_limited")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please retry in {retry_after} seconds.",
        )

    user = get_user_by_email(db, email)
    if not user or not verify_password(req.password, user.password_hash):
        is_locked = record_failed_attempt(f"login_fail_{email}", max_failures=5, lockout_seconds=300)
        record_login_event(db, email, ip, False, user_id=user.id if user else None, user_agent=user_agent, failure_reason="bad_credentials")
        db.commit()
        detail = "Account temporarily locked due to failed attempts. Try in 5 minutes." if is_locked else "Invalid email or password."
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

    clear_failed_attempts(f"login_fail_{email}")

    # Generate tokens
    access_token = create_access_token(user.id, user.email, is_admin=user.is_admin, expires_in_minutes=15)
    raw_refresh = generate_random_token(32)
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=30)

    # Save session with hashed refresh token
    create_auth_session(
        db,
        user_id=user.id,
        refresh_token=raw_refresh,
        expires_at=refresh_expires,
        user_agent=user_agent[:512],
        ip_address=ip[:45],
        device_label="Web Browser",
    )
    record_login_event(db, email, ip, True, user_id=user.id, user_agent=user_agent)
    db.commit()

    _set_auth_cookies(response, access_token, raw_refresh)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "is_verified": user.is_verified,
            "is_admin": user.is_admin,
        },
        "message": "Logged in successfully.",
    }


@router.post("/demo-login")
def demo_login(request: Request, response: Response, db: Session = Depends(get_db)):
    """Instant login for demonstration and research evaluation without requiring signup."""
    demo_email = "demo@safarsathi.in"
    demo_pass = "DemoExplorer2026!"

    user = get_user_by_email(db, demo_email)
    if not user:
        hashed_pw = hash_password(demo_pass)
        user = create_user(db, email=demo_email, password_hash=hashed_pw, is_verified=True)
        profile = get_or_create_profile(db, user.id)
        profile.home_city = "Nagpur"
        profile.travel_style = "balanced"
        profile.budget_range = "mid"
        profile.diet_preference = "veg"
        db.commit()
    else:
        if not user.is_verified:
            user.is_verified = True
            db.commit()

    ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent", "Demo Session")

    access_token = create_access_token(user.id, user.email, is_admin=False, expires_in_minutes=60)
    raw_refresh = generate_random_token(32)
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=30)

    create_auth_session(
        db,
        user_id=user.id,
        refresh_token=raw_refresh,
        expires_at=refresh_expires,
        user_agent=user_agent[:512],
        ip_address=ip[:45],
        device_label="Demo Mode Session",
    )
    db.commit()

    _set_auth_cookies(response, access_token, raw_refresh)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "is_verified": user.is_verified,
            "is_admin": user.is_admin,
        },
        "message": "Demo mode active. Logged in as demo traveler.",
    }


@router.post("/refresh")
def refresh_session(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """Rotate refresh token and issue a new access token in httpOnly cookies."""
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required")

    session = get_active_auth_session(db, refresh_token)
    if not session:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked session")

    user = get_user_by_id(db, session.user_id)
    if not user or not user.is_active:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    # Rotate refresh token
    new_refresh = generate_random_token(32)
    session.refresh_token_hash = hash_token(new_refresh)
    session.last_seen_at = datetime.now(timezone.utc)
    session.expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    access_token = create_access_token(user.id, user.email, is_admin=user.is_admin, expires_in_minutes=15)
    db.commit()

    _set_auth_cookies(response, access_token, new_refresh)

    return {"message": "Session refreshed"}


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke active session and clear cookies."""
    if refresh_token:
        session = get_active_auth_session(db, refresh_token)
        if session and session.user_id == current_user.id:
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()

    _clear_auth_cookies(response)
    return {"message": "Logged out successfully", "logged_out": True}


@router.post("/logout-all")
def logout_all(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke all active sessions for current user."""
    count = revoke_all_user_sessions(db, current_user.id)
    db.commit()
    _clear_auth_cookies(response)
    return {"message": f"Revoked {count} active sessions", "sessions_revoked": count}


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Request password reset link with rate limiting. Returns generic message."""
    ip = request.client.host if request.client else "unknown"
    allowed, retry_after = check_rate_limit(f"forgot_{ip}", max_requests=5, window_seconds=60)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Please wait {retry_after} seconds.")

    email = req.email.strip().casefold()
    user = get_user_by_email(db, email)
    if user:
        raw_token = generate_random_token()
        exp = datetime.now(timezone.utc) + timedelta(hours=2)
        db.add(EmailToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            token_type="reset_password",
            expires_at=exp,
        ))
        db.commit()
        send_password_reset_email(email, raw_token)

    return {"message": "If that email exists in our records, a password reset link has been dispatched."}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using verified token."""
    if len(req.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")

    token_h = hash_token(req.token.strip())
    now = datetime.now(timezone.utc)
    
    email_token = db.query(EmailToken).filter(
        EmailToken.token_hash == token_h,
        EmailToken.token_type == "reset_password",
        EmailToken.used_at.is_(None),
        EmailToken.expires_at > now,
    ).first()

    if not email_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token.")

    user = get_user_by_id(db, email_token.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found.")

    user.password_hash = hash_password(req.new_password)
    email_token.used_at = now
    # Invalidate all prior sessions on password reset
    revoke_all_user_sessions(db, user.id)
    db.commit()

    return {"message": "Password updated successfully. Please log in with your new password."}


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change password for currently authenticated user."""
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password incorrect.")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be at least 8 characters.")

    current_user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "Password changed successfully."}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return current authenticated user profile."""
    profile = get_or_create_profile(db, current_user.id)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at,
        "profile": {
            "home_city": profile.home_city,
            "diet_preference": profile.diet_preference,
            "allergies": profile.allergies,
            "travel_style": profile.travel_style,
            "budget_range": profile.budget_range,
            "interests": profile.interests,
            "consent_location": profile.consent_location,
            "consent_contacts": profile.consent_contacts,
        },
    }


@router.get("/sessions")
def list_active_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all active sessions for current user."""
    now = datetime.now(timezone.utc)
    sessions = db.query(AuthSession).filter(
        AuthSession.user_id == current_user.id,
        AuthSession.revoked_at.is_(None),
        AuthSession.expires_at > now,
    ).order_by(AuthSession.last_seen_at.desc()).all()

    return [
        {
            "id": s.id,
            "device_label": s.device_label or "Web Browser",
            "ip_address": s.ip_address,
            "created_at": s.created_at,
            "last_seen_at": s.last_seen_at,
        }
        for s in sessions
    ]


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke a specific session with ownership check."""
    revoked = revoke_auth_session(db, session_id, current_user.id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    db.commit()
    return {"message": "Session revoked", "revoked": True}


@router.get("/login-history")
def get_login_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get 90-day login audit log for current user."""
    events = db.query(LoginEvent).filter(
        LoginEvent.user_id == current_user.id
    ).order_by(LoginEvent.created_at.desc()).limit(30).all()

    return [
        {
            "id": e.id,
            "ip_address": e.ip_address,
            "user_agent": e.user_agent,
            "success": e.success,
            "failure_reason": e.failure_reason,
            "created_at": e.created_at,
        }
        for e in events
    ]


@router.get("/export-data")
def export_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Download complete user data package (GDPR/Privacy export)."""
    profile = get_or_create_profile(db, current_user.id)
    contacts = list_trusted_contacts(db, current_user.id)
    convos = list_conversations(db, current_user.id, limit=100)
    trips = list_trips(db, current_user.id, limit=100)

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
        },
        "profile": {
            "home_city": profile.home_city,
            "diet_preference": profile.diet_preference,
            "allergies": profile.allergies,
            "travel_style": profile.travel_style,
            "budget_range": profile.budget_range,
            "interests": profile.interests,
        },
        "trusted_contacts": contacts,
        "conversations": [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in convos],
        "trips": [{"id": t.id, "destination": t.destination, "title": t.title, "data": t.data_json} for t in trips],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/account")
def delete_account(
    req: DeleteAccountRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hard delete account and all cascade data. Requires password confirmation."""
    if not verify_password(req.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password incorrect.")

    delete_user(db, current_user.id)
    db.commit()
    _clear_auth_cookies(response)

    return {"message": "Account permanently deleted.", "deleted": True}
