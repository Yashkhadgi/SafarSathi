"""B10: Transport extension — train/bus info and stay area recommendations.

All train and timing info is approximate. Responses include 'IRCTC par verify karein' note.
No booking links are provided.
"""

import json
from pathlib import Path

_KB_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"

_IRCTC_NOTE = (
    "\n\n📌 IRCTC par verify karein (irctc.co.in) ya railway enquiry 139 par call karein "
    "for current schedules, availability, and fares before travel. "
    "All timings above are approximate and subject to change."
)


def _load_kb_records():
    records = []
    try:
        for json_file in _KB_PATH.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        records.extend(data)
            except Exception:
                pass
    except Exception:
        pass
    return records


def _find_records(query_terms: list, category: str):
    """Return records matching any query term and the given category."""
    records = _load_kb_records()
    results = []
    for rec in records:
        if rec.get("category", "").casefold() != category.casefold():
            continue
        text_fields = " ".join([
            rec.get("place", ""),
            rec.get("state", ""),
            rec.get("text", ""),
        ]).casefold()
        if any(term.casefold() in text_fields for term in query_terms):
            results.append(rec)
    return results


def get_train_bus_info(origin: str, destination: str) -> dict:
    """Return train and bus route information between two cities.

    Info only — no booking links. All timings are approximate.
    Includes 'IRCTC par verify karein' note.

    Args:
        origin: Departure city.
        destination: Destination city.

    Returns:
        dict with route info, approx timings, and IRCTC verification note.
    """
    try:
        origin = str(origin or "").strip()
        destination = str(destination or "").strip()
        if not origin or not destination:
            return {"error": "Both origin and destination are required"}

        # Search KB for records about origin or destination
        query_terms = [origin, destination]
        records = _find_records(query_terms, "train_bus_routes")

        if not records:
            return {
                "origin": origin,
                "destination": destination,
                "info": (
                    f"No specific train/bus route data found in our knowledge base for {origin} to {destination}. "
                    "Check IRCTC (irctc.co.in) for train options or Redbus for bus options."
                ),
                "irctc_note": _IRCTC_NOTE,
                "booking_note": "No booking links provided. Use official IRCTC or state roadway websites to book.",
                "railway_enquiry": "139",
            }

        # Combine relevant text from matched records
        combined_info = []
        sources = []
        for rec in records:
            combined_info.append(rec.get("text", ""))
            if rec.get("source_name"):
                sources.append({"name": rec["source_name"], "url": rec.get("source_url", "")})

        return {
            "origin": origin,
            "destination": destination,
            "route_info": "\n\n".join(combined_info) + _IRCTC_NOTE,
            "irctc_note": _IRCTC_NOTE,
            "booking_note": "No booking links provided. Use official IRCTC or state roadway websites to book.",
            "railway_enquiry": "139",
            "sources": sources[:3],
        }
    except Exception as exc:
        return {"error": f"Train/bus info lookup failed: {exc}"}


def get_stay_areas(city: str, traveler_type: str = "") -> dict:
    """Return accommodation zone recommendations for a city.

    Args:
        city: Destination city.
        traveler_type: Optional — 'backpacker', 'family', 'solo', 'women_solo', 'senior', 'business'.

    Returns:
        dict with stay area recommendations and guidance.
    """
    try:
        city = str(city or "").strip()
        traveler_type = str(traveler_type or "").strip().lower()
        if not city:
            return {"error": "City name is required"}

        records = _find_records([city], "stay_areas")

        if not records:
            return {
                "city": city,
                "traveler_type": traveler_type,
                "info": (
                    f"No stay-area data found in our knowledge base for {city}. "
                    "General tip: stay near the railway station for early train access, "
                    "or in the central tourist district for walkability."
                ),
                "booking_note": "No booking links provided. Use MakeMyTrip, Booking.com, or hotel websites directly.",
            }

        # Filter or annotate for traveler type
        text_blocks = []
        for rec in records:
            text = rec.get("text", "")
            text_blocks.append(text)

        combined = "\n\n".join(text_blocks)

        # Add traveler-type specific tip
        traveler_tips = {
            "backpacker": "💡 Backpacker tip: Look for hostels and guesthouses in the budget zones mentioned above.",
            "family": "💡 Family tip: Prefer mid-range hotels with pools in quieter residential zones. Early breakfast is common.",
            "solo": "💡 Solo tip: Hostels in backpacker zones have good social scenes. Check reviews for solo safety.",
            "women_solo": "💡 Women solo tip: Choose established hotels with 24-hour reception. Avoid isolated guesthouses. Many hotels have women-only floors.",
            "senior": "💡 Senior tip: Mid-range or premium hotels with lifts and accessible rooms in main tourist zones reduce walking distance.",
            "business": "💡 Business tip: Look for hotels near business districts or with good metro/cab access.",
            "disabled": "💡 Accessibility tip: Verify lift access, ramps, and accessible bathrooms directly with the hotel — not all Indian properties have full accessibility.",
        }
        tip = traveler_tips.get(traveler_type, "")

        sources = []
        for rec in records[:3]:
            if rec.get("source_name"):
                sources.append({"name": rec["source_name"], "url": rec.get("source_url", "")})

        return {
            "city": city,
            "traveler_type": traveler_type or "general",
            "stay_areas": combined,
            "traveler_tip": tip,
            "booking_note": "No booking links provided. Use MakeMyTrip, Booking.com, or hotel websites directly.",
            "sources": sources,
        }
    except Exception as exc:
        return {"error": f"Stay areas lookup failed: {exc}"}
