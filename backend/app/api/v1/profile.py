"""Profile and Trusted Contacts API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.models.user import User
from backend.app.repositories.profile_repo import (
    add_trusted_contact,
    delete_trusted_contact,
    get_or_create_profile,
    list_trusted_contacts,
    update_profile,
)

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdateRequest(BaseModel):
    home_city: Optional[str] = None
    diet_preference: Optional[str] = None
    allergies: Optional[List[str]] = None
    travel_style: Optional[str] = None
    budget_range: Optional[str] = None
    mobility_notes: Optional[str] = None
    interests: Optional[List[str]] = None
    consent_location: Optional[bool] = None
    consent_contacts: Optional[bool] = None


class AddContactRequest(BaseModel):
    name: str
    phone: str
    relationship_label: Optional[str] = None


@router.get("")
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's profile and preferences."""
    profile = get_or_create_profile(db, current_user.id)
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "home_city": profile.home_city,
        "diet_preference": profile.diet_preference,
        "allergies": profile.allergies,
        "travel_style": profile.travel_style,
        "budget_range": profile.budget_range,
        "mobility_notes": profile.mobility_notes,
        "interests": profile.interests,
        "consent_location": profile.consent_location,
        "consent_contacts": profile.consent_contacts,
    }


@router.put("")
def put_update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile preferences with ownership verification."""
    profile = update_profile(
        db=db,
        user_id=current_user.id,
        home_city=req.home_city,
        diet_preference=req.diet_preference,
        allergies=req.allergies,
        travel_style=req.travel_style,
        budget_range=req.budget_range,
        mobility_notes=req.mobility_notes,
        interests=req.interests,
        consent_location=req.consent_location,
        consent_contacts=req.consent_contacts,
    )
    db.commit()
    return {"message": "Profile updated successfully.", "profile": {
        "home_city": profile.home_city,
        "diet_preference": profile.diet_preference,
        "allergies": profile.allergies,
        "travel_style": profile.travel_style,
        "budget_range": profile.budget_range,
    }}


# --- Trusted Contacts (Max 3 contacts, encrypted phone numbers) ---

@router.get("/contacts")
def get_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List trusted emergency contacts for current user (phone decrypted)."""
    contacts = list_trusted_contacts(db, current_user.id)
    return contacts


@router.post("/contacts", status_code=status.HTTP_201_CREATED)
def post_add_contact(
    req: AddContactRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a trusted contact (max 3 allowed; encrypted at rest)."""
    existing = list_trusted_contacts(db, current_user.id)
    if len(existing) >= 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 3 trusted contacts allowed.")

    if not req.name.strip() or not req.phone.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name and phone number required.")

    contact = add_trusted_contact(
        db=db,
        user_id=current_user.id,
        name=req.name.strip(),
        phone=req.phone.strip(),
        relationship_label=req.relationship_label,
    )
    db.commit()
    return {"id": contact.id, "name": contact.name, "message": "Contact added securely."}


@router.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a trusted contact with ownership verification."""
    deleted = delete_trusted_contact(db, contact_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found.")
    db.commit()
    return {"message": "Contact deleted", "deleted": True}
