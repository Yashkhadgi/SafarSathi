"""FastAPI Dependencies: DB session and User Authentication from Cookie / Bearer header."""

from typing import Generator, Optional
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from backend.app.db.session import SessionLocal
from backend.app.core.security import verify_access_token
from backend.app.db.models.user import User
from backend.app.repositories.user_repo import get_user_by_id


def get_db() -> Generator:
    """Yield a database session and safely close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_optional(
    request: Request,
    access_token_cookie: Optional[str] = Cookie(default=None, alias="access_token"),
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Retrieve current authenticated user from cookie or Authorization header. Returns None if unauthenticated."""
    token = None
    if access_token_cookie:
        token = access_token_cookie
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        return None

    payload = verify_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        return None

    return user


def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Require an authenticated user. Raises 401 if missing/invalid."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Require an authenticated admin user. Raises 403 if not admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user
