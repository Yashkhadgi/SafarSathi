"""Repository for User and AuthSession operations with strict ownership enforcement."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.db.models.user import User, AuthSession, LoginEvent, EmailToken
from backend.app.core.security import hash_token


def _now():
    return datetime.now(timezone.utc)


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Fetch user by ID."""
    return db.query(User).filter(User.id == str(user_id)).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Fetch user by email (case-insensitive)."""
    return db.query(User).filter(User.email == str(email).strip().casefold()).first()


def create_user(db: Session, email: str, password_hash: str, is_verified: bool = False, is_admin: bool = False) -> User:
    """Create a new user with default blank profile."""
    user = User(
        email=str(email).strip().casefold(),
        password_hash=password_hash,
        is_verified=is_verified,
        is_admin=is_admin,
    )
    db.add(user)
    db.flush()
    return user


def ensure_user_exists(db: Session, user_id: str) -> User:
    """Ensure a user record exists for this user_id; create anonymous user if missing."""
    user = get_user_by_id(db, user_id)
    if not user:
        user = User(
            id=str(user_id),
            email=f"anon_{user_id[:8]}@safarsathi.local",
            password_hash="[none]",
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        db.flush()
    return user


def delete_user(db: Session, user_id: str) -> bool:
    """Hard delete user and all cascading rows (sessions, chats, trips, contacts, profile, feedback)."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.flush()
    return True


def record_login_event(
    db: Session,
    email: str,
    ip_address: str,
    success: bool,
    user_id: Optional[str] = None,
    user_agent: Optional[str] = None,
    failure_reason: Optional[str] = None,
) -> LoginEvent:
    """Log an authentication event for security auditing."""
    event = LoginEvent(
        user_id=user_id,
        email_attempted=str(email).strip().casefold(),
        ip_address=ip_address or "unknown",
        user_agent=user_agent,
        success=success,
        failure_reason=failure_reason,
    )
    db.add(event)
    db.flush()
    return event


def create_auth_session(
    db: Session,
    user_id: str,
    refresh_token: str,
    expires_at: datetime,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    device_label: Optional[str] = None,
) -> AuthSession:
    """Create a new auth session storing only the hash of the refresh token."""
    session = AuthSession(
        user_id=user_id,
        refresh_token_hash=hash_token(refresh_token),
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
        device_label=device_label,
    )
    db.add(session)
    db.flush()
    return session


def get_active_auth_session(db: Session, refresh_token: str) -> Optional[AuthSession]:
    """Retrieve an active, non-revoked auth session by refresh token."""
    token_h = hash_token(refresh_token)
    return db.query(AuthSession).filter(
        AuthSession.refresh_token_hash == token_h,
        AuthSession.revoked_at.is_(None),
        AuthSession.expires_at > _now(),
    ).first()


def revoke_auth_session(db: Session, session_id: str, user_id: str) -> bool:
    """Revoke an active auth session with ownership check."""
    session = db.query(AuthSession).filter(
        AuthSession.id == session_id,
        AuthSession.user_id == user_id,
    ).first()
    if not session:
        return False
    session.revoked_at = _now()
    db.flush()
    return True


def revoke_all_user_sessions(db: Session, user_id: str) -> int:
    """Revoke all active sessions for a user."""
    count = db.query(AuthSession).filter(
        AuthSession.user_id == user_id,
        AuthSession.revoked_at.is_(None),
    ).update({"revoked_at": _now()})
    db.flush()
    return count
