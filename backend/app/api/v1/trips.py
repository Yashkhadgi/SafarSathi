"""Trips and Itineraries API endpoints with version history and export."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.models.user import User
from backend.app.repositories.trip_repo import (
    create_trip,
    delete_trip,
    get_trip,
    list_trips,
    save_trip_version,
    undo_trip_version,
)
from tools.export_tool import export_itinerary

router = APIRouter(prefix="/trips", tags=["trips"])


class SaveTripRequest(BaseModel):
    title: Optional[str] = None
    conversation_id: Optional[str] = None
    data: Dict[str, Any]


class UpdateTripRequest(BaseModel):
    data: Dict[str, Any]
    change_summary: Optional[str] = "Updated plan"


class ExportTripRequest(BaseModel):
    format_type: str = "text"  # 'text', 'ics', 'pdf'


@router.get("")
def get_trips(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all saved itineraries for current user."""
    trips = list_trips(db, current_user.id, limit=limit, offset=offset)
    return [
        {
            "id": t.id,
            "title": t.title,
            "destination": t.destination,
            "duration_days": t.duration_days,
            "current_version": t.current_version,
            "updated_at": t.updated_at,
            "data": t.data_json,
        }
        for t in trips
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def post_create_trip(
    req: SaveTripRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a new travel itinerary."""
    trip = create_trip(
        db=db,
        user_id=current_user.id,
        data=req.data,
        title=req.title,
        conversation_id=req.conversation_id,
    )
    db.commit()
    return {
        "id": trip.id,
        "title": trip.title,
        "destination": trip.destination,
        "version": trip.current_version,
        "data": trip.data_json,
    }


@router.get("/{trip_id}")
def get_trip_details(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get trip details and immutable version history with ownership check."""
    trip = get_trip(db, trip_id, current_user.id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found.")

    versions = [
        {
            "version": v.version,
            "change_summary": v.change_summary,
            "created_at": v.created_at,
        }
        for v in trip.versions
    ]
    return {
        "id": trip.id,
        "title": trip.title,
        "destination": trip.destination,
        "duration_days": trip.duration_days,
        "current_version": trip.current_version,
        "data": trip.data_json,
        "versions": versions,
        "updated_at": trip.updated_at,
    }


@router.patch("/{trip_id}")
def patch_update_trip(
    trip_id: str,
    req: UpdateTripRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save an updated version of a trip with change summary."""
    updated = save_trip_version(
        db=db,
        trip_id=trip_id,
        user_id=current_user.id,
        data=req.data,
        change_summary=req.change_summary or "Updated plan",
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found.")
    db.commit()
    return {"id": updated.id, "version": updated.current_version, "data": updated.data_json}


@router.post("/{trip_id}/undo")
def post_undo_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Undo latest edit and restore the previous version."""
    restored = undo_trip_version(db, trip_id, current_user.id)
    if not restored:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot undo: no previous version found.")
    db.commit()
    return {"id": restored.id, "version": restored.current_version, "data": restored.data_json}


@router.delete("/{trip_id}")
def delete_trip_by_id(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a trip with ownership check."""
    deleted = delete_trip(db, trip_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found.")
    db.commit()
    return {"message": "Trip deleted", "deleted": True}


@router.post("/{trip_id}/export")
def export_trip_by_id(
    trip_id: str,
    req: ExportTripRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export trip as text (WhatsApp), .ics (Calendar), or PDF summary."""
    trip = get_trip(db, trip_id, current_user.id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found.")

    result = export_itinerary(format_type=req.format_type, trip_data=trip.data_json)
    return result
