"""B9: Entry fees tool — monument entry fees lookup from data/budget/entry_fees.json."""

import json
from pathlib import Path

_FEES_PATH = Path(__file__).resolve().parents[1] / "data" / "budget" / "entry_fees.json"


def _load_fees():
    """Load entry fees data. Returns None on failure."""
    try:
        with open(_FEES_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def get_entry_fees(place: str) -> dict:
    """Return entry fee information for a monument or city.

    Args:
        place: Monument name or city name.

    Returns:
        dict with fee info, free days, timings, and source. All prices are approx.
    """
    try:
        place = str(place or "").strip()
        if not place:
            return {"error": "Place or monument name is required"}

        data = _load_fees()
        if data is None:
            return {"error": "Entry fees data not available"}

        place_lower = place.casefold()
        monuments = data.get("monuments", [])

        # Exact or partial match on place name or city
        matches = []
        for m in monuments:
            if (place_lower in m.get("place", "").casefold()
                    or place_lower in m.get("city", "").casefold()
                    or m.get("place", "").casefold() in place_lower):
                matches.append(m)

        if not matches:
            return {
                "place": place,
                "message": (
                    f"No entry fee data found for '{place}' in our records. "
                    "Verify current fees at ASI (asi.nic.in) or the specific monument website."
                ),
                "source": data.get("source_name", "ASI"),
                "source_url": data.get("source_url", "https://asi.nic.in/"),
                "last_verified": data.get("last_verified", "2024-10"),
                "disclaimer": data.get("disclaimer", "Fees are approximate; verify before visiting."),
            }

        results = []
        for m in matches:
            results.append({
                "monument": m.get("place"),
                "city": m.get("city"),
                "state": m.get("state"),
                "entry_fee_indian_inr": m.get("entry_fee_indian_inr"),
                "entry_fee_foreign_inr_approx": m.get("entry_fee_foreign_inr_approx"),
                "free_for": m.get("free_for"),
                "free_days": m.get("free_days"),
                "closed_day": m.get("closed_day"),
                "timings": m.get("timings"),
                "notes": m.get("notes"),
                "approx": True,
                "last_verified": m.get("last_verified", data.get("last_verified")),
                "source": m.get("source_name", data.get("source_name")),
                "source_url": m.get("source_url", data.get("source_url")),
            })

        res = {
            "place": place,
            "results": results,
            "disclaimer": data.get("disclaimer", "All fees are approximate — verify at monument."),
            "last_verified": data.get("last_verified", "2024-10"),
        }
        res["ui"] = {
            "type": "price_table",
            "version": "1.0",
            "data": {
                "city_or_place": place,
                "kind": "monument_entry",
                "items": [
                    {
                        "label": r.get("monument"),
                        "price_inr": str(r.get("entry_fee_indian_inr", "verify")),
                        "foreign_price_inr": str(r.get("entry_fee_foreign_inr_approx", "verify")),
                        "free_days": r.get("free_days") or r.get("free_for", "None"),
                        "source_url": r.get("source_url", ""),
                        "last_verified": r.get("last_verified", "2024-10"),
                    }
                    for r in results
                ],
                "disclaimer": res["disclaimer"],
            }
        }
        return res
    except Exception as exc:
        return {"error": f"Entry fees lookup failed: {exc}"}

