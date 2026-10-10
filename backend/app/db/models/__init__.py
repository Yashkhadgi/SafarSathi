"""Export all models for Alembic and SQLAlchemy metadata."""

from backend.app.db.models.user import User, AuthSession, LoginEvent, EmailToken, OAuthAccount
from backend.app.db.models.conversation import Conversation, Message
from backend.app.db.models.trip import Trip, TripVersion
from backend.app.db.models.profile import Profile
from backend.app.db.models.contact import TrustedContact
from backend.app.db.models.feedback import Feedback

__all__ = [
    "User",
    "AuthSession",
    "LoginEvent",
    "EmailToken",
    "OAuthAccount",
    "Conversation",
    "Message",
    "Trip",
    "TripVersion",
    "Profile",
    "TrustedContact",
    "Feedback",
]
