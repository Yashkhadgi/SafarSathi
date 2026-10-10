"""B13: Recommender tool — destination recommender and best-time-to-visit lookups.

Scoring is pure Python calculation — no LLM math.
"""

import json
import math
from pathlib import Path

_KB_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"

# Destination data for scoring (lat, lon, best_months, tags, typical_budget_tier)
_DESTINATIONS = {
    "Goa": {
        "lat": 15.2993, "lon": 74.1240,
        "best_months": [11, 12, 1, 2, 3],
        "tags": ["beach", "party", "heritage", "honeymoon", "solo"],
        "budget_per_day_inr": {"backpacker": 1500, "mid": 3500, "luxury": 8000},
        "min_days": 3, "max_days": 10,
    },
    "Jaipur": {
        "lat": 26.9124, "lon": 75.7873,
        "best_months": [10, 11, 12, 1, 2, 3],
        "tags": ["heritage", "culture", "family", "honeymoon", "solo"],
        "budget_per_day_inr": {"backpacker": 1200, "mid": 2800, "luxury": 7000},
        "min_days": 2, "max_days": 5,
    },
    "Manali": {
        "lat": 32.2432, "lon": 77.1892,
        "best_months": [3, 4, 5, 6, 10, 11],
        "tags": ["adventure", "mountain", "trek", "honeymoon", "solo", "nature"],
        "budget_per_day_inr": {"backpacker": 1500, "mid": 3000, "luxury": 7000},
        "min_days": 4, "max_days": 8,
    },
    "Leh": {
        "lat": 34.1526, "lon": 77.5771,
        "best_months": [5, 6, 7, 8, 9],
        "tags": ["adventure", "mountain", "trek", "culture", "spiritual", "solo", "backpacking"],
        "budget_per_day_inr": {"backpacker": 2000, "mid": 4000, "luxury": 9000},
        "min_days": 5, "max_days": 10,
    },
    "Varanasi": {
        "lat": 25.3176, "lon": 82.9739,
        "best_months": [10, 11, 12, 1, 2, 3],
        "tags": ["spiritual", "pilgrimage", "culture", "heritage", "solo", "photography"],
        "budget_per_day_inr": {"backpacker": 800, "mid": 2000, "luxury": 5000},
        "min_days": 2, "max_days": 4,
    },
    "Kerala": {
        "lat": 10.8505, "lon": 76.2711,
        "best_months": [10, 11, 12, 1, 2, 3],
        "tags": ["backwaters", "nature", "honeymoon", "family", "wildlife", "spiritual", "food"],
        "budget_per_day_inr": {"backpacker": 1500, "mid": 3500, "luxury": 9000},
        "min_days": 5, "max_days": 14,
    },
    "Agra": {
        "lat": 27.1767, "lon": 78.0081,
        "best_months": [10, 11, 12, 1, 2, 3],
        "tags": ["heritage", "UNESCO", "family", "culture", "honeymoon"],
        "budget_per_day_inr": {"backpacker": 1000, "mid": 2500, "luxury": 7000},
        "min_days": 1, "max_days": 3,
    },
    "Udaipur": {
        "lat": 24.5854, "lon": 73.7125,
        "best_months": [9, 10, 11, 12, 1, 2, 3],
        "tags": ["heritage", "lake", "honeymoon", "culture", "romantic", "family"],
        "budget_per_day_inr": {"backpacker": 1200, "mid": 3000, "luxury": 9000},
        "min_days": 2, "max_days": 4,
    },
    "Rishikesh": {
        "lat": 30.0869, "lon": 78.2676,
        "best_months": [3, 4, 5, 9, 10, 11],
        "tags": ["adventure", "yoga", "spiritual", "rafting", "trek", "solo", "backpacking"],
        "budget_per_day_inr": {"backpacker": 800, "mid": 2000, "luxury": 5000},
        "min_days": 3, "max_days": 7,
    },
    "Darjeeling": {
        "lat": 27.0360, "lon": 88.2627,
        "best_months": [3, 4, 5, 9, 10, 11],
        "tags": ["mountain", "tea", "heritage", "nature", "honeymoon", "solo", "photography"],
        "budget_per_day_inr": {"backpacker": 1200, "mid": 2800, "luxury": 7000},
        "min_days": 3, "max_days": 6,
    },
    "Hampi": {
        "lat": 15.3350, "lon": 76.4600,
        "best_months": [10, 11, 12, 1, 2, 3],
        "tags": ["heritage", "UNESCO", "backpacking", "photography", "solo", "ruins"],
        "budget_per_day_inr": {"backpacker": 700, "mid": 1800, "luxury": 4000},
        "min_days": 2, "max_days": 4,
    },
    "Mysuru": {
        "lat": 12.2958, "lon": 76.6394,
        "best_months": [9, 10, 11, 12, 1, 2],
        "tags": ["heritage", "culture", "family", "palace", "food", "yoga"],
        "budget_per_day_inr": {"backpacker": 900, "mid": 2200, "luxury": 5500},
        "min_days": 2, "max_days": 4,
    },
    "Amritsar": {
        "lat": 31.6340, "lon": 74.8723,
        "best_months": [10, 11, 12, 1, 2, 3],
        "tags": ["spiritual", "pilgrimage", "heritage", "food", "culture"],
        "budget_per_day_inr": {"backpacker": 900, "mid": 2000, "luxury": 5000},
        "min_days": 1, "max_days": 3,
    },
}

# City coordinates for distance calculation (origin city lookup)
_CITY_COORDS = {
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "kolkata": (22.5726, 88.3639),
    "chennai": (13.0827, 80.2707),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "goa": (15.2993, 74.1240),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _budget_tier(budget_inr: float, days: int) -> str:
    """Determine budget tier from total budget and days."""
    if days <= 0:
        days = 1
    daily = budget_inr / days
    if daily < 1800:
        return "backpacker"
    if daily < 5000:
        return "mid"
    return "luxury"


def _score_destination(name: str, dest: dict, budget_inr: float, days: int,
                        month: int, mood: str, origin_lat: float, origin_lon: float) -> float:
    """Score a destination 0-100 using Python arithmetic only."""
    score = 0.0

    # 1. Mood/tag match (0-30 pts, prioritize explicit user interests)
    mood_words = [w.strip().lower() for w in mood.replace(",", " ").split() if len(w.strip()) > 2]
    if mood_words:
        matched_tags = 0
        for mw in mood_words:
            if any(mw in t or t in mw for t in dest["tags"]):
                matched_tags += 1
        if matched_tags > 0:
            score += min(30.0, matched_tags * 15.0)
    else:
        score += 15.0  # neutral if no mood specified

    # 2. Season match (0-25 pts)
    if month in dest["best_months"]:
        score += 25.0
    elif any(abs(month - m) <= 1 or abs(month - m) >= 11 for m in dest["best_months"]):
        score += 12.0  # adjacent month

    # 3. Budget fit (0-25 pts)
    daily_budget = budget_inr / max(days, 1)
    tier_costs = dest["budget_per_day_inr"]
    # If the daily budget covers mid-range or backpacker easily, award full points
    if daily_budget >= tier_costs.get("mid", 3000):
        score += 25.0
    elif daily_budget >= tier_costs.get("backpacker", 1500):
        score += 20.0
    else:
        # Tight budget
        ratio = daily_budget / max(tier_costs.get("backpacker", 1500), 1)
        score += max(0.0, 20.0 * ratio)

    # 4. Trip length fit (0-15 pts)
    if dest["min_days"] <= days <= dest["max_days"]:
        score += 15.0
    elif days < dest["min_days"]:
        score += max(0.0, 15.0 - (dest["min_days"] - days) * 4.0)
    else:
        score += max(0.0, 15.0 - (days - dest["max_days"]) * 2.5)

    # 5. Distance penalty / preference (0-5 pts)
    if origin_lat and origin_lon:
        dist_km = _haversine_km(origin_lat, origin_lon, dest["lat"], dest["lon"])
        dist_score = max(0.0, 5.0 * (1.0 - dist_km / 3500.0))
        score += dist_score

    return round(score, 2)


def recommend_destinations(budget_inr: float, days: int, month: int, mood: str,
                            origin_city: str, top_n: int = 3) -> dict:
    """Recommend top destinations using pure Python scoring.

    Args:
        budget_inr: Total trip budget in INR.
        days: Number of travel days.
        month: Travel month (1=January, 12=December).
        mood: Travel mood/preference (e.g., 'adventure', 'heritage', 'beach', 'spiritual').
        origin_city: Traveler's departure city (for distance scoring).
        top_n: Number of recommendations to return.

    Returns:
        dict with ranked destination recommendations.
    """
    try:
        budget_inr = float(budget_inr or 0)
        days = int(days or 3)
        month = int(month or 1)
        top_n = int(top_n or 3)
        origin_city = str(origin_city or "").strip().lower()
        mood = str(mood or "").strip()

        if budget_inr <= 0:
            return {"error": "budget_inr must be a positive number"}
        if not (1 <= month <= 12):
            return {"error": "month must be between 1 and 12"}
        if days <= 0:
            return {"error": "days must be a positive integer"}

        # Resolve origin city coordinates
        origin_coords = _CITY_COORDS.get(origin_city, (20.5937, 78.9629))  # default: India center
        origin_lat, origin_lon = origin_coords

        scored = []
        for name, dest in _DESTINATIONS.items():
            s = _score_destination(name, dest, budget_inr, days, month, mood, origin_lat, origin_lon)
            tier = _budget_tier(budget_inr, days)
            est_cost = dest["budget_per_day_inr"].get(tier, 3000) * days
            scored.append({
                "destination": name,
                "score": s,
                "estimated_cost_inr": est_cost,
                "budget_tier": tier,
                "best_months": dest["best_months"],
                "tags": dest["tags"],
                "recommended_days": f"{dest['min_days']}-{dest['max_days']}",
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:top_n]

        return {
            "budget_inr": budget_inr,
            "days": days,
            "month": month,
            "mood": mood,
            "origin_city": origin_city,
            "recommendations": top,
            "disclaimer": "Scores are approximate Python calculations based on budget fit, seasonality, and tag match. Verify current conditions before booking.",
            "scoring_method": "Python arithmetic (budget_fit + season_match + trip_length_fit + mood_match + distance_score)",
        }
    except Exception as exc:
        return {"error": f"Destination recommendation failed: {exc}"}


def best_time_to_visit(place: str) -> dict:
    """Return best time to visit a destination from KB data.

    Args:
        place: Destination name (city, state, or region).

    Returns:
        dict with best months, festivals, and source.
    """
    try:
        place = str(place or "").strip()
        if not place:
            return {"error": "Place name is required"}

        # Check internal destination data first
        place_lower = place.casefold()
        for name, dest in _DESTINATIONS.items():
            if name.casefold() == place_lower or place_lower in name.casefold():
                months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                best_month_names = [months[m - 1] for m in dest["best_months"]]
                return {
                    "place": name,
                    "best_months": dest["best_months"],
                    "best_months_names": best_month_names,
                    "source": "SafarSathi destination database",
                }

        # Fall back to KB best_time records
        try:
            records = []
            for json_file in _KB_PATH.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        if isinstance(data, list):
                            for rec in data:
                                if (rec.get("category") == "best_time"
                                        and place_lower in rec.get("place", "").casefold()):
                                    records.append(rec)
                except Exception:
                    pass
        except Exception:
            records = []

        if records:
            rec = records[0]
            return {
                "place": rec.get("place", place),
                "best_time_info": rec.get("text", ""),
                "source": rec.get("source_name", ""),
                "source_url": rec.get("source_url", ""),
                "last_verified": rec.get("last_verified", ""),
            }

        return {
            "place": place,
            "info": f"No specific best-time data for '{place}'. General guidance: avoid peak summer (Apr-Jun) and monsoon (Jul-Sep) unless specifically seeking those experiences.",
        }
    except Exception as exc:
        return {"error": f"Best time lookup failed: {exc}"}


_KB_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"
