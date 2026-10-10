"""Feedback API endpoint for turn evaluation."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.rate_limit import check_rate_limit
from backend.app.db.models.user import User
from backend.app.repositories.profile_repo import create_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    rating: int  # 1 for thumbs up, -1 for thumbs down
    reason: Optional[str] = None  # 'wrong_info', 'too_long', 'language_error', 'other'
    comment: Optional[str] = None
    tools_used: Optional[List[str]] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    req: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit user feedback for an AI response turn."""
    allowed, retry_after = check_rate_limit(f"feedback_{current_user.id}", max_requests=20, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many feedback submissions. Please wait {retry_after} seconds.",
        )

    if req.rating not in (1, -1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be 1 (positive) or -1 (negative).")

    fb = create_feedback(
        db=db,
        user_id=current_user.id,
        rating=req.rating,
        conversation_id=req.conversation_id,
        message_id=req.message_id,
        reason=req.reason,
        comment=req.comment,
        tools_used=req.tools_used,
    )
    db.commit()

    return {"message": "Thank you for your feedback.", "feedback_id": fb.id}
