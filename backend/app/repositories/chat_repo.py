"""Repository for Conversation and Message operations with strict ownership enforcement."""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from backend.app.db.models.conversation import Conversation, Message
from backend.app.repositories.user_repo import ensure_user_exists


def _now():
    return datetime.now(timezone.utc)


def create_conversation(db: Session, user_id: str, title: str = "New chat", language: str = "en") -> Conversation:
    """Create a new conversation for a user."""
    ensure_user_exists(db, user_id)
    convo = Conversation(
        user_id=str(user_id),
        title=(title or "New chat").strip()[:150],
        language=language or "en",
    )
    db.add(convo)
    db.flush()
    return convo


def get_conversation(db: Session, conversation_id: str, user_id: str) -> Optional[Conversation]:
    """Get a conversation with ownership check. Returns None if not owned by user."""
    return db.query(Conversation).filter(
        Conversation.id == str(conversation_id),
        Conversation.user_id == str(user_id),
    ).first()


def list_conversations(
    db: Session, user_id: str, limit: int = 50, offset: int = 0, search: Optional[str] = None
) -> List[Conversation]:
    """List paginated conversations for a user with optional title search."""
    query = db.query(Conversation).filter(Conversation.user_id == str(user_id))
    if search:
        query = query.filter(Conversation.title.ilike(f"%{search.strip()}%"))
    return query.order_by(desc(Conversation.updated_at)).offset(offset).limit(limit).all()


def update_conversation_title(db: Session, conversation_id: str, user_id: str, title: str) -> Optional[Conversation]:
    """Update conversation title with ownership verification."""
    convo = get_conversation(db, conversation_id, user_id)
    if not convo:
        return None
    convo.title = str(title).strip()[:150] or "New chat"
    convo.updated_at = _now()
    db.flush()
    return convo


def delete_conversation(db: Session, conversation_id: str, user_id: str) -> bool:
    """Delete conversation and all messages with ownership check."""
    convo = get_conversation(db, conversation_id, user_id)
    if not convo:
        return False
    db.delete(convo)
    db.flush()
    return True


def save_message(
    db: Session,
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    tools_used: Optional[List[str]] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
    cards: Optional[List[Dict[str, Any]]] = None,
    language: str = "en",
) -> Message:
    """Append a message turn to a conversation and bump updated_at."""
    # Ensure conversation exists and belongs to user
    convo = get_conversation(db, conversation_id, user_id)
    if not convo:
        convo = create_conversation(db, user_id, title=content[:60] or "New chat", language=language)
        conversation_id = convo.id
    elif convo.title == "New chat" and role == "user" and content:
        convo.title = content.strip()[:60]

    convo.updated_at = _now()

    msg = Message(
        conversation_id=conversation_id,
        user_id=str(user_id),
        role=role,
        content=content,
        tools_used=tools_used or [],
        sources=sources or [],
        cards=cards or [],
        language=language or "en",
    )
    db.add(msg)
    db.flush()
    return msg


def get_messages(
    db: Session, conversation_id: str, user_id: str, limit: int = 50, offset: int = 0
) -> Tuple[List[Message], int]:
    """Get paginated messages for a conversation with ownership check. Returns (messages, total_count)."""
    convo = get_conversation(db, conversation_id, user_id)
    if not convo:
        return [], 0

    total = db.query(Message).filter(Message.conversation_id == str(conversation_id)).count()
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == str(conversation_id))
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return msgs, total


def search_messages(db: Session, user_id: str, query: str, limit: int = 20) -> List[Message]:
    """Search user's messages for text content (ownership isolated)."""
    if not query:
        return []
    return (
        db.query(Message)
        .filter(
            Message.user_id == str(user_id),
            Message.content.ilike(f"%{query.strip()}%"),
        )
        .order_by(desc(Message.created_at))
        .limit(limit)
        .all()
    )
