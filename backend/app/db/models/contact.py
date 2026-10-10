"""TrustedContact model with phone number encrypted at rest."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship
from backend.app.db.base import Base


def _now():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class TrustedContact(Base):
    __tablename__ = "trusted_contacts"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    phone_encrypted = Column(Text, nullable=False)  # Encrypted at rest via Fernet / security.py
    relationship_label = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    user = relationship("User", back_populates="trusted_contacts")

    __table_args__ = (
        Index("idx_trusted_contacts_user", "user_id"),
    )
