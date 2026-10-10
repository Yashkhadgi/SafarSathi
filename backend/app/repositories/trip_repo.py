"""Repository for Trip and TripVersion operations with strict ownership enforcement."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.db.models.trip import Trip, TripVersion
from backend.app.repositories.user_repo import ensure_user_exists


def _now():
    return datetime.now(timezone.utc)


def create_trip(
    db: Session,
    user_id: str,
    data: Dict[str, Any],
    title: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Trip:
    """Create a new trip and its initial immutable version 1."""
    ensure_user_exists(db, user_id)
    dest = data.get("destination", "Trip")
    trip_title = (title or dest)[:150]
    days = data.get("days", [])
    duration = len(days) if days else int(data.get("duration_days", 1))

    trip = Trip(
        user_id=str(user_id),
        conversation_id=str(conversation_id) if conversation_id else None,
        title=trip_title,
        destination=dest,
        duration_days=duration,
        data_json=data,
        current_version=1,
    )
    db.add(trip)
    db.flush()

    # Create version 1
    v1 = TripVersion(
        trip_id=trip.id,
        version=1,
        change_summary="Initial plan",
        data_json=data,
    )
    db.add(v1)
    db.flush()

    # Annotate trip id into payload
    data["trip_id"] = trip.id
    data["version"] = 1
    trip.data_json = data
    db.flush()

    return trip


def get_trip(db: Session, trip_id: str, user_id: str) -> Optional[Trip]:
    """Fetch trip with ownership verification. Returns None if not owned by user."""
    return db.query(Trip).filter(
        Trip.id == str(trip_id),
        Trip.user_id == str(user_id),
    ).first()


def list_trips(db: Session, user_id: str, limit: int = 50, offset: int = 0) -> List[Trip]:
    """List all trips owned by a user."""
    return (
        db.query(Trip)
        .filter(Trip.user_id == str(user_id))
        .order_by(desc(Trip.updated_at))
        .offset(offset)
        .limit(limit)
        .all()
    )


def save_trip_version(
    db: Session, trip_id: str, user_id: str, data: Dict[str, Any], change_summary: str
) -> Optional[Trip]:
    """Increment version and record immutable version history with ownership check."""
    trip = get_trip(db, trip_id, user_id)
    if not trip:
        return None

    new_version = trip.current_version + 1
    data["trip_id"] = trip.id
    data["version"] = new_version

    trip.current_version = new_version
    trip.data_json = data
    trip.updated_at = _now()

    version_record = TripVersion(
        trip_id=trip.id,
        version=new_version,
        change_summary=(change_summary or "Updated plan")[:255],
        data_json=data,
    )
    db.add(version_record)
    db.flush()
    return trip


def undo_trip_version(db: Session, trip_id: str, user_id: str) -> Optional[Trip]:
    """Restore the previous version of a trip."""
    trip = get_trip(db, trip_id, user_id)
    if not trip or trip.current_version <= 1:
        return None

    target_version_num = trip.current_version - 1
    prev_version = (
        db.query(TripVersion)
        .filter(TripVersion.trip_id == trip.id, TripVersion.version == target_version_num)
        .first()
    )
    if not prev_version:
        return None

    return save_trip_version(
        db, trip_id, user_id, dict(prev_version.data_json), f"Undo back to version {target_version_num}"
    )


def delete_trip(db: Session, trip_id: str, user_id: str) -> bool:
    """Delete a trip and its version history with ownership check."""
    trip = get_trip(db, trip_id, user_id)
    if not trip:
        return False
    db.delete(trip)
    db.flush()
    return True
