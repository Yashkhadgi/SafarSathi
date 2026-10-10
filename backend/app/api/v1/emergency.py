"""Public Emergency endpoint (zero LLM dependency, cached static emergency data)."""

import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(tags=["emergency"])

_EMERGENCY_PATH = Path(__file__).resolve().parents[4] / "data" / "emergency" / "india.json"
_PHRASES_PATH = Path(__file__).resolve().parents[4] / "data" / "emergency" / "phrases.json"


def _load_static_emergency():
    """Load pre-compiled static emergency numbers and phrases."""
    data = {
        "national_emergency": "112",
        "police": "100",
        "ambulance": "108",
        "fire": "101",
        "women_helpline": "1091",
        "tourist_police_helpline": "1363",
        "child_helpline": "1098",
        "railway_enquiry": "139",
        "last_verified": "2024-10-15",
        "source": "Government of India National Emergency Number (112.gov.in)",
    }
    if _EMERGENCY_PATH.exists():
        try:
            with open(_EMERGENCY_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data.update(loaded)
        except Exception:
            pass
    return data


@router.get("/emergency")
def get_emergency_info():
    """Public emergency numbers and offline guidance. Requires no authentication."""
    return {
        "emergency_numbers": _load_static_emergency(),
        "disclaimer": "Dial 112 immediately in any life-threatening situation. This information is for general guidance.",
        "offline_ready": True,
    }
