"""Repository for Traveler Profile, Trusted Contacts (encrypted), and Feedback."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.db.models.profile import Profile
from backend.app.db.models.contact import TrustedContact
from backend.app.db.models.feedback import Feedback
from backend.app.core.security import encrypt_phone, decrypt_phone
from backend.app.repositories.user_repo import ensure_user_exists


def _now():
    return datetime.now(timezone.utc)


# --- Profile Operations ---

def get_or_create_profile(db: Session, user_id: str) -> Profile:
    """Get user profile or create a default blank profile."""
    ensure_user_exists(db, user_id)
    profile = db.query(Profile).filter(Profile.user_id == str(user_id)).first()
    if not profile:
        profile = Profile(
            user_id=str(user_id),
            diet_preference="all",
            allergies=[],
            travel_style="normal",
            budget_range="mid",
            interests=[],
            consent_location=False,
            consent_contacts=False,
        )
        db.add(profile)
        db.flush()
    return profile


def update_profile(
    db: Session,
    user_id: str,
    home_city: Optional[str] = None,
    diet_preference: Optional[str] = None,
    allergies: Optional[List[str]] = None,
    travel_style: Optional[str] = None,
    budget_range: Optional[str] = None,
    mobility_notes: Optional[str] = None,
    interests: Optional[List[str]] = None,
    consent_location: Optional[bool] = None,
    consent_contacts: Optional[bool] = None,
) -> Profile:
    """Update profile attributes with ownership verification."""
    profile = get_or_create_profile(db, user_id)
    if home_city is not None:
        profile.home_city = str(home_city).strip()[:100]
    if diet_preference is not None:
        profile.diet_preference = str(diet_preference).strip().lower()
    if allergies is not None:
        profile.allergies = allergies
    if travel_style is not None:
        profile.travel_style = str(travel_style).strip().lower()
    if budget_range is not None:
        profile.budget_range = str(budget_range).strip().lower()
    if mobility_notes is not None:
        profile.mobility_notes = str(mobility_notes).strip()
    if interests is not None:
        profile.interests = interests
    if consent_location is not None:
        profile.consent_location = bool(consent_location)
    if consent_contacts is not None:
        profile.consent_contacts = bool(consent_contacts)
    
    profile.updated_at = _now()
    db.flush()
    return profile


# --- Trusted Contacts Operations (Encrypted at rest) ---

def add_trusted_contact(
    db: Session, user_id: str, name: str, phone: str, relationship_label: Optional[str] = None
) -> TrustedContact:
    """Add a trusted contact, automatically encrypting the phone number with Fernet."""
    ensure_user_exists(db, user_id)
    encrypted_phone = encrypt_phone(str(phone).strip())
    contact = TrustedContact(
        user_id=str(user_id),
        name=str(name).strip()[:100],
        phone_encrypted=encrypted_phone,
        relationship_label=str(relationship_label).strip()[:50] if relationship_label else None,
    )
    db.add(contact)
    db.flush()
    return contact


def list_trusted_contacts(db: Session, user_id: str) -> List[Dict[str, Any]]:
    """List trusted contacts for a user with phone numbers decrypted for display."""
    rows = db.query(TrustedContact).filter(TrustedContact.user_id == str(user_id)).all()
    results = []
    for r in rows:
        results.append({
            "id": r.id,
            "user_id": r.user_id,
            "name": r.name,
            "phone": decrypt_phone(r.phone_encrypted),
            "relationship_label": r.relationship_label,
            "created_at": r.created_at,
        })
    return results


def delete_trusted_contact(db: Session, contact_id: str, user_id: str) -> bool:
    """Delete a trusted contact with ownership check."""
    contact = db.query(TrustedContact).filter(
        TrustedContact.id == str(contact_id),
        TrustedContact.user_id == str(user_id),
    ).first()
    if not contact:
        return False
    db.delete(contact)
    db.flush()
    return True


# --- Feedback Operations ---

def create_feedback(
    db: Session,
    user_id: str,
    rating: int,
    conversation_id: Optional[str] = None,
    message_id: Optional[str] = None,
    reason: Optional[str] = None,
    comment: Optional[str] = None,
    tools_used: Optional[List[str]] = None,
) -> Feedback:
    """Record user feedback turn evaluation."""
    ensure_user_exists(db, user_id)
    fb = Feedback(
        user_id=str(user_id),
        conversation_id=str(conversation_id) if conversation_id else None,
        message_id=str(message_id) if message_id else None,
        rating=rating,
        reason=str(reason).strip()[:100] if reason else None,
        comment=str(comment).strip() if comment else None,
        tools_used=tools_used or [],
    )
    db.add(fb)
    db.flush()
    return fb
