"""Chat and Conversation API endpoints with Server-Sent Events (SSE)."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.rate_limit import check_rate_limit
from backend.app.db.models.user import User
from backend.app.repositories.chat_repo import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_messages,
    list_conversations,
    search_messages,
    update_conversation_title,
)
from backend.app.services.agent_adapter import stream_agent_chat

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    language: Optional[str] = "en"


class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New chat"
    language: Optional[str] = "en"


class RenameConversationRequest(BaseModel):
    title: str


@router.post("", response_class=StreamingResponse)
async def post_chat_stream(
    req: ChatMessageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Server-Sent Events (SSE) endpoint for conversational chat streaming.

    Streams token deltas, status messages, tool activity, and citations.
    """
    # Rate limit check per user (max 30 queries per minute)
    allowed, retry_after = check_rate_limit(f"chat_{current_user.id}", max_requests=30, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please wait {retry_after} seconds.",
        )

    msg_text = req.message.strip()
    if not msg_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty.")

    # Resolve or create conversation
    convo_id = req.conversation_id
    if convo_id:
        convo = get_conversation(db, convo_id, current_user.id)
        if not convo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    else:
        convo = create_conversation(db, current_user.id, title=msg_text[:50], language=req.language or "en")
        convo_id = convo.id
        db.commit()

    async def event_generator():
        async for item in stream_agent_chat(
            db=db,
            user=current_user,
            conversation_id=convo_id,
            user_message=msg_text,
            language=req.language or "en",
        ):
            event_type = item.get("event", "message")
            data_str = json.dumps(item.get("data", {}), ensure_ascii=False)
            yield f"event: {event_type}\ndata: {data_str}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# --- Conversation Management ---

@router.get("/conversations")
def get_conversations(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List paginated conversations for current user with optional title filter."""
    convos = list_conversations(db, current_user.id, limit=limit, offset=offset, search=search)
    return [
        {
            "id": c.id,
            "title": c.title,
            "language": c.language,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in convos
    ]


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def post_create_conversation(
    req: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new conversation thread."""
    convo = create_conversation(db, current_user.id, title=req.title or "New chat", language=req.language or "en")
    db.commit()
    return {
        "id": convo.id,
        "title": convo.title,
        "language": convo.language,
        "created_at": convo.created_at,
    }


@router.get("/conversations/{conversation_id}")
def get_conversation_details(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get conversation messages (paginated) with ownership check."""
    convo = get_conversation(db, conversation_id, current_user.id)
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    msgs, total = get_messages(db, conversation_id, current_user.id, limit=limit, offset=offset)
    return {
        "conversation": {
            "id": convo.id,
            "title": convo.title,
            "language": convo.language,
            "created_at": convo.created_at,
            "updated_at": convo.updated_at,
        },
        "total_messages": total,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tools_used": m.tools_used,
                "sources": m.sources,
                "cards": m.cards or [],
                "created_at": m.created_at,
            }
            for m in msgs
        ],
    }


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages_only(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Direct messages getter for a conversation."""
    convo = get_conversation(db, conversation_id, current_user.id)
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    msgs, total = get_messages(db, conversation_id, current_user.id, limit=limit, offset=offset)
    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tools_used": m.tools_used,
                "sources": m.sources,
                "cards": m.cards or [],
                "created_at": m.created_at,
            }
            for m in msgs
        ],
        "total": total,
    }


@router.patch("/conversations/{conversation_id}")
def patch_rename_conversation(
    conversation_id: str,
    req: RenameConversationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rename conversation title with ownership verification."""
    convo = update_conversation_title(db, conversation_id, current_user.id, req.title)
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    db.commit()
    return {"id": convo.id, "title": convo.title}


@router.delete("/conversations/{conversation_id}")
def delete_conversation_by_id(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete conversation and all messages with ownership verification."""
    deleted = delete_conversation(db, conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    db.commit()
    return {"message": "Conversation deleted", "deleted": True}


@router.get("/conversations/{conversation_id}/export")
def export_conversation(
    conversation_id: str,
    export_format: str = Query(default="markdown", enum=["markdown", "json"]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export conversation history in Markdown or JSON format."""
    convo = get_conversation(db, conversation_id, current_user.id)
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    msgs, _ = get_messages(db, conversation_id, current_user.id, limit=500)
    if export_format == "json":
        return {
            "conversation_id": convo.id,
            "title": convo.title,
            "created_at": convo.created_at.isoformat(),
            "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in msgs],
        }

    # Markdown format
    lines = [f"# {convo.title}\n*Exported from SafarSathi on {convo.created_at.strftime('%Y-%m-%d')}*\n"]
    for m in msgs:
        prefix = "**You**:" if m.role == "user" else "**SafarSathi Assistant**:"
        lines.append(f"{prefix}\n{m.content}\n")
    return {"content": "\n".join(lines), "format": "markdown", "filename": f"safarsathi_chat_{convo.id[:8]}.md"}


@router.get("/search")
def search_chat_history(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search messages in user's chat history."""
    results = search_messages(db, current_user.id, q, limit=limit)
    return [
        {
            "message_id": m.id,
            "conversation_id": m.conversation_id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at,
        }
        for m in results
    ]
