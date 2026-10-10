"""Adapter bridging agents/core_agent.py and tools/registry.py with FastAPI SSE streaming."""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.db.models.user import User
from backend.app.repositories.profile_repo import get_or_create_profile
from backend.app.repositories.chat_repo import save_message, get_messages

_logger = logging.getLogger("safarsathi.agent_adapter")


def build_profile_summary(db: Session, user_id: str) -> str:
    """Format user profile attributes into a compact guidance prompt."""
    profile = get_or_create_profile(db, user_id)
    notes = []
    if profile.home_city:
        notes.append(f"Home city: {profile.home_city}")
    if profile.diet_preference and profile.diet_preference != "all":
        notes.append(f"Diet: {profile.diet_preference} (strictly respect this)")
    if profile.allergies:
        notes.append(f"Allergies: {', '.join(profile.allergies)}")
    if profile.mobility_notes:
        notes.append(f"Mobility/Accessibility: {profile.mobility_notes}")
    if profile.travel_style and profile.travel_style != "normal":
        notes.append(f"Pace: {profile.travel_style}")
    return "; ".join(notes)


async def stream_agent_chat(
    db: Session,
    user: User,
    conversation_id: str,
    user_message: str,
    language: str = "en",
) -> AsyncGenerator[Dict[str, Any], None]:
    """Execute the core agent pipeline and yield formatted Server-Sent Events.

    Yields events with keys:
      - event: 'status' | 'token' | 'sources' | 'tools_used' | 'done' | 'error'
      - data: dict payload
    """
    # 1. Save user message to database
    user_msg_obj = save_message(
        db=db,
        conversation_id=conversation_id,
        user_id=user.id,
        role="user",
        content=user_message,
        language=language,
    )
    db.commit()

    yield {
        "event": "status",
        "data": {"message": "Processing your query...", "step": "start"},
    }

    try:
        from agents.core_agent import stream_core_agent
        from tools.registry import TOOL_FUNCTIONS

        # Use session_id format: "{user_id}:{conversation_id}"
        session_id = f"{user.id}:{conversation_id}"
        full_assistant_reply = []
        collected_sources = []
        collected_tools = []

        # Run streaming core agent generator
        for chunk in stream_core_agent(session_id=session_id, message=user_message):
            if not isinstance(chunk, dict):
                continue

            if "status" in chunk:
                yield {
                    "event": "status",
                    "data": {"message": chunk["status"], "step": "tool_execution"},
                }

            if "partial" in chunk:
                token_text = chunk["partial"]
                full_assistant_reply.append(token_text)
                yield {
                    "event": "token",
                    "data": {"delta": token_text},
                }

            if "sources" in chunk and isinstance(chunk["sources"], list):
                collected_sources.extend(chunk["sources"])
                yield {
                    "event": "sources",
                    "data": {"sources": chunk["sources"]},
                }

            if "tools_used" in chunk and isinstance(chunk["tools_used"], list):
                collected_tools.extend(chunk["tools_used"])
                yield {
                    "event": "tools_used",
                    "data": {"tools": chunk["tools_used"]},
                }

            # Small yield pause for async event loop responsiveness
            await asyncio.sleep(0.01)

        final_content = "".join(full_assistant_reply).strip()
        if not final_content:
            final_content = "I have processed your travel request. Please let me know how else I can assist."

        # 2. Save assistant response to database
        asst_msg_obj = save_message(
            db=db,
            conversation_id=conversation_id,
            user_id=user.id,
            role="assistant",
            content=final_content,
            tools_used=list(dict.fromkeys(collected_tools)),
            sources=collected_sources,
            language=language,
        )
        db.commit()

        yield {
            "event": "done",
            "data": {
                "message_id": asst_msg_obj.id,
                "conversation_id": conversation_id,
                "content": final_content,
                "tools_used": asst_msg_obj.tools_used,
                "sources": asst_msg_obj.sources,
            },
        }

    except Exception as exc:
        _logger.exception("Chat stream execution failed: %s", exc)
        fallback_content = f"I encountered an issue processing this request: {exc}. Emergency numbers: 112 (National), 108 (Ambulance)."
        
        err_msg = save_message(
            db=db,
            conversation_id=conversation_id,
            user_id=user.id,
            role="assistant",
            content=fallback_content,
            language=language,
        )
        db.commit()

        yield {
            "event": "error",
            "data": {"error": str(exc), "fallback_message_id": err_msg.id, "content": fallback_content},
        }
