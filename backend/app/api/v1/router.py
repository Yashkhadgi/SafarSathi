"""Main API v1 Router aggregator mounting all Phase 2 endpoints."""

from fastapi import APIRouter
from backend.app.api.v1 import auth, chat, emergency, feedback, health, profile, tools, trips, voice

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health.router)
api_v1_router.include_router(emergency.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(chat.router)
api_v1_router.include_router(trips.router)
api_v1_router.include_router(profile.router)
api_v1_router.include_router(voice.router)
api_v1_router.include_router(feedback.router)
api_v1_router.include_router(tools.tools_router)
