"""Traveler Profile model with diet, mobility, and consent preferences."""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.app.db.base import Base


def _now():
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    home_city = Column(String(100), nullable=True)
    diet_preference = Column(String(50), nullable=False, default="all")  # 'veg', 'vegan', 'jain', 'halal', 'all'
    allergies = Column(JSON, nullable=False, default=list)
    travel_style = Column(String(50), nullable=False, default="normal")  # 'relaxed', 'normal', 'packed'
    budget_range = Column(String(50), nullable=False, default="mid")     # 'backpacker', 'mid', 'luxury'
    mobility_notes = Column(Text, nullable=True)
    interests = Column(JSON, nullable=False, default=list)
    consent_location = Column(Boolean, nullable=False, default=False)
    consent_contacts = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user = relationship("User", back_populates="profile")
