"""Trip and TripVersion models for versioned, owned travel plans."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import relationship
from backend.app.db.base import Base


def _now():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Trip(Base):
    __tablename__ = "trips"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(150), nullable=False)
    destination = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=True)
    duration_days = Column(Integer, nullable=False, default=1)
    data_json = Column(JSON, nullable=False)
    current_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user = relationship("User", back_populates="trips")
    conversation = relationship("Conversation")
    versions = relationship("TripVersion", back_populates="trip", cascade="all, delete-orphan", order_by="TripVersion.version")

    __table_args__ = (
        Index("idx_trips_user_updated", "user_id", "updated_at"),
    )


class TripVersion(Base):
    __tablename__ = "trip_versions"

    id = Column(String(36), primary_key=True, default=_uuid)
    trip_id = Column(String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    change_summary = Column(String(255), nullable=False)
    data_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    trip = relationship("Trip", back_populates="versions")

    __table_args__ = (
        Index("idx_trip_versions_trip_version", "trip_id", "version", unique=True),
    )
