"""User feedback model for message evaluations."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.app.db.base import Base


def _now():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    rating = Column(Integer, nullable=False)  # +1 (positive), -1 (negative)
    reason = Column(String(100), nullable=True)  # 'wrong_info', 'too_long', 'language_error', 'other'
    comment = Column(Text, nullable=True)
    tools_used = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    user = relationship("User", back_populates="feedback")
    conversation = relationship("Conversation", back_populates="feedback")
    message = relationship("Message")

    __table_args__ = (
        Index("idx_feedback_user_created", "user_id", "created_at"),
    )
