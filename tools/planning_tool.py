"""B12: Planning tool — theme trip weights, traveler-type notes, and Plan B alternatives.

All logic is pure Python — no LLM math.
"""


# Theme → KB tag weights for scoring/filtering knowledge base records
_THEME_WEIGHTS = {
    "spiritual": {"tags": ["pilgrimage", "temple", "ghat", "aarti", "yoga", "ashram", "sacred"], "weight": 2.0},
    "adventure": {"tags": ["trek", "trekking", "rafting", "camping", "bungee", "zip", "mountain", "himalaya", "adventure", "paragliding"], "weight": 2.0},
    "honeymoon": {"tags": ["romantic", "lake", "backwaters", "houseboat", "sunset", "heritage_hotel", "beach", "luxury"], "weight": 2.0},
    "family": {"tags": ["family", "kids", "wildlife", "zoo", "theme_park", "fort", "palace", "beach", "boating"], "weight": 1.5},
    "solo": {"tags": ["hostel", "backpacker", "budget", "solo", "cafe", "trek", "rooftop"], "weight": 1.5},
    "backpacking": {"tags": ["budget", "hostel", "backpacker", "cheap", "guesthouse", "local_transport", "street_food"], "weight": 1.5},
    "heritage": {"tags": ["heritage", "fort", "palace", "monument", "UNESCO", "haveli", "ruins", "history", "museum"], "weight": 2.0},
    "wildlife": {"tags": ["wildlife", "safari", "national_park", "tiger", "elephant", "bird", "reserve", "jungle"], "weight": 2.0},
    "food": {"tags": ["food", "street_food", "cuisine", "restaurant", "thali", "local_cuisine", "market", "bazaar"], "weight": 2.0},
}

# Traveler-type notes for pace/accessibility
_TRAVELER_TYPE_NOTES = {
    "kids": {
        "pace": "relaxed",
        "max_stops_per_day": 2,
        "notes": (
            "Plan short, engaging activities. Avoid sites with very long queues in heat. "
            "Water/snack breaks every 2 hours. Choose hotels with pools or playgrounds. "
            "Avoid mountain roads (prone to altitude/motion sickness)."
        ),
        "accessibility": "Standard; avoid extreme altitude destinations for young children.",
    },
    "senior": {
        "pace": "relaxed",
        "max_stops_per_day": 2,
        "notes": (
            "Relaxed pace essential. Avoid cobblestones and uneven terrain where possible. "
            "Book sites with priority/senior queues (many ASI monuments have them). "
            "Ensure accommodation has lifts. Carry sufficient medication. "
            "Avoid Ladakh/high altitude unless medically cleared."
        ),
        "accessibility": "Check for ramps and lift access at hotels. Many heritage sites lack modern accessibility.",
    },
    "disabled": {
        "pace": "relaxed",
        "max_stops_per_day": 2,
        "notes": (
            "Verify wheelchair ramps and lift access at specific monuments before visiting — "
            "many historical sites (forts, temples) were not built with accessibility in mind. "
            "Some museums (National Museum Delhi, Victoria Memorial Kolkata) have improved accessibility. "
            "App-based taxis are generally accessible. Plan rest points."
        ),
        "accessibility": "Verify monument-specific accessibility before confirming itinerary. Some sites have limited access.",
    },
    "women_solo": {
        "pace": "normal",
        "max_stops_per_day": 3,
        "notes": (
            "Choose established accommodation with 24-hour reception. "
            "Use app-based taxis (Ola/Uber) over street hailing, especially at night. "
            "Avoid remote areas alone after dark. "
            "Trust instincts — leave situations that feel uncomfortable. "
            "Women-only metro coaches available in Delhi, Mumbai, Kolkata, Jaipur. "
            "Tourist police helpline: 1363. Emergency: 112."
        ),
        "accessibility": "Standard.",
    },
    "group": {
        "pace": "packed",
        "max_stops_per_day": 4,
        "notes": (
            "Book transportation (bus/van) in advance for groups of 6+. "
            "Group discounts available at many monuments — check at entry. "
            "Assign a group coordinator for entry tickets and headcounts. "
            "Large groups may need multiple restaurant reservations in advance."
        ),
        "accessibility": "Standard; ensure transport fits group size.",
    },
}

# Plan B indoor/rainy-day alternatives per activity type
_PLAN_B_ALTERNATIVES = {
    "outdoor_sightseeing": [
        "Visit a nearby museum (national/state museums are usually indoors)",
        "Explore covered heritage bazaars or shopping arcades",
        "Cultural performance or classical music event (check local listings)",
        "Cooking class or local cuisine workshop",
    ],
    "beach": [
        "Beach shack lunch/dinner (covered seating usually available)",
        "Spice plantation or coconut grove tour with covered areas",
        "Old Goa churches and cathedrals (indoor heritage)",
        "Casino (Goa has licensed floating casinos)",
        "Yoga or Ayurveda session at a wellness centre",
    ],
    "trek": [
        "Tea/coffee plantation visit with covered walkways",
        "Local craft demonstration or artisan workshop",
        "Monastery or temple interior visit",
        "Museum or heritage interpretation centre",
        "Day trip by road to a covered attraction in valley",
    ],
    "desert": [
        "Jaisalmer Fort interior (covered sections)",
        "Haveli museum tour",
        "Puppet show or folk music performance (often in covered venues)",
        "Local textile or handicraft shop exploration",
    ],
    "wildlife_safari": [
        "Wildlife photography exhibit or nature documentary at resort",
        "Jungle walk cancelled — try the resort's nature library or bird-watching from covered areas",
        "Tribal art or crafts workshop at nearby village (weather permitting)",
    ],
    "default": [
        "Visit a well-reviewed restaurant and try local cuisine",
        "Browse local handicraft markets or malls",
        "Visit a museum or art gallery",
        "Rest and plan next day at hotel",
        "Watch a cultural performance or film at a local theatre",
    ],
}


def theme_trip_weights(theme: str) -> dict:
    """Return KB tag weights and associated activity tags for a travel theme.

    Args:
        theme: One of: spiritual, adventure, honeymoon, family, solo, backpacking, heritage, wildlife, food.

    Returns:
        dict with tags, weights, and suggested KB categories.
    """
    try:
        theme = str(theme or "").strip().lower()
        if not theme:
            return {"error": "Theme is required", "valid_themes": list(_THEME_WEIGHTS.keys())}

        if theme not in _THEME_WEIGHTS:
            return {
                "error": f"Unknown theme: '{theme}'",
                "valid_themes": list(_THEME_WEIGHTS.keys()),
            }

        data = _THEME_WEIGHTS[theme]
        return {
            "theme": theme,
            "priority_tags": data["tags"],
            "weight": data["weight"],
            "suggested_kb_categories": ["top_sights", "food_guide", "best_time", "overview"],
            "note": "Use these tags to filter/score knowledge base records when building a themed itinerary.",
        }
    except Exception as exc:
        return {"error": f"Theme weights lookup failed: {exc}"}


def traveler_type_notes(traveler_type: str) -> dict:
    """Return pace and accessibility notes for a traveler type.

    Args:
        traveler_type: One of: kids, senior, disabled, women_solo, group.

    Returns:
        dict with recommended pace, max stops per day, practical notes.
    """
    try:
        traveler_type = str(traveler_type or "").strip().lower()
        if not traveler_type:
            return {"error": "Traveler type is required", "valid_types": list(_TRAVELER_TYPE_NOTES.keys())}

        if traveler_type not in _TRAVELER_TYPE_NOTES:
            return {
                "error": f"Unknown traveler type: '{traveler_type}'",
                "valid_types": list(_TRAVELER_TYPE_NOTES.keys()),
            }

        data = _TRAVELER_TYPE_NOTES[traveler_type]
        return {
            "traveler_type": traveler_type,
            "recommended_pace": data["pace"],
            "max_stops_per_day": data["max_stops_per_day"],
            "practical_notes": data["notes"],
            "accessibility_note": data["accessibility"],
        }
    except Exception as exc:
        return {"error": f"Traveler type notes lookup failed: {exc}"}


def plan_b_alternatives(itinerary: dict, weather_data: dict) -> dict:
    """Return indoor or rainy-day alternative activities per day of an itinerary.

    Logic is pure Python — no LLM.

    Args:
        itinerary: Trip dictionary with 'days' list (from build_itinerary).
        weather_data: Optional weather dict; if rain probability > 60% or condition contains 'rain', plan B triggers.

    Returns:
        dict with per-day alternatives and trigger reason.
    """
    try:
        if not isinstance(itinerary, dict):
            return {"error": "itinerary must be a dict (from build_itinerary)"}

        destination = itinerary.get("destination", "")
        days = itinerary.get("days", [])
        if not days:
            return {"error": "Itinerary has no days to generate Plan B for"}

        # Determine weather trigger
        rain_triggered = False
        trigger_reason = "manual request"
        if isinstance(weather_data, dict):
            rain_prob = weather_data.get("rain_probability", 0)
            condition = str(weather_data.get("condition", "")).lower()
            if rain_prob > 60 or "rain" in condition or "storm" in condition or "flood" in condition:
                rain_triggered = True
                trigger_reason = f"rain/weather alert ({condition or f'{rain_prob}% rain probability'})"

        # Build per-day plan B
        day_alternatives = []
        for day in days:
            day_num = day.get("day", "?")
            slots = day.get("slots", [])
            # Guess activity type from slot names
            activity_type = "default"
            all_names = " ".join(s.get("place", "") for s in slots).lower()
            if any(kw in all_names for kw in ["beach", "sea", "coast", "goa"]):
                activity_type = "beach"
            elif any(kw in all_names for kw in ["trek", "trail", "hike", "peak", "valley"]):
                activity_type = "trek"
            elif any(kw in all_names for kw in ["desert", "dune", "jaisalmer", "thar"]):
                activity_type = "desert"
            elif any(kw in all_names for kw in ["tiger", "safari", "wildlife", "jungle", "park", "reserve"]):
                activity_type = "wildlife_safari"
            elif destination.lower() in ("goa",):
                activity_type = "beach"

            alternatives = _PLAN_B_ALTERNATIVES.get(activity_type, _PLAN_B_ALTERNATIVES["default"])
            day_alternatives.append({
                "day": day_num,
                "original_activities": [s.get("place") for s in slots],
                "activity_type_detected": activity_type,
                "plan_b_alternatives": alternatives,
            })

        return {
            "destination": destination,
            "rain_triggered": rain_triggered,
            "trigger_reason": trigger_reason,
            "days": day_alternatives,
            "note": "Plan B alternatives are general suggestions — verify availability locally.",
        }
    except Exception as exc:
        return {"error": f"Plan B generation failed: {exc}"}
