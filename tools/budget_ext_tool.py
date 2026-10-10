"""B9 extension: Fair-price checker and ATM info using data/budget/fair_prices.json."""

import json
from pathlib import Path

_PRICES_PATH = Path(__file__).resolve().parents[1] / "data" / "budget" / "fair_prices.json"

_ATM_INFO = {
    "general": (
        "ATMs from major banks (SBI, HDFC, ICICI, Axis, PNB) are widely available in Indian cities. "
        "International cards (Visa, Mastercard) work at most ATMs. Withdrawal limit is typically INR 10,000-20,000 per transaction. "
        "Forex cards and traveler's cheques can be exchanged at authorised money changers or bank branches. "
        "Always use ATMs inside banks or malls rather than standalone kiosks to reduce skimming risk."
    ),
    "per_city": {
        "leh": "ATMs in Leh town centre are available but connectivity can be intermittent — carry enough cash before venturing to Pangong, Nubra, or Zanskar.",
        "goa": "ATMs are plentiful in North and South Goa tourist areas; remote beaches may have no ATM for several km.",
        "jaisalmer": "ATMs available in main market area; carry cash for desert camp and remote sites.",
        "varanasi": "ATMs near Godaulia and Cantonment area are reliable; ghat lanes have few ATMs.",
    }
}


def _load_prices():
    try:
        with open(_PRICES_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def check_fair_price(city: str, transport_type: str = "", context: str = "") -> dict:
    """Return fair price reference for transport and meals in a city.

    All figures are approximate (approx) planning references.

    Args:
        city: City name.
        transport_type: Optional — 'auto', 'taxi', 'bus', 'metro', 'boat', 'train'.
        context: Optional additional context.

    Returns:
        dict with price ranges and disclaimer.
    """
    try:
        city = str(city or "").strip()
        if not city:
            return {"error": "City name is required"}

        data = _load_prices()
        if data is None:
            return {"error": "Fair price data not available"}

        city_lower = city.casefold()
        cities = data.get("cities", {})

        # Find city key case-insensitively
        city_key = None
        for k in cities:
            if k.casefold() == city_lower:
                city_key = k
                break

        if city_key is None:
            return {
                "city": city,
                "message": (
                    f"No fair-price data found for '{city}'. "
                    "General guidance: negotiate auto fares before boarding, use app-based taxis for transparency. "
                    "All prices vary by season and demand."
                ),
                "source": data.get("source_name", ""),
                "disclaimer": data.get("disclaimer", ""),
                "last_verified": data.get("last_verified", "2024-10"),
            }

        city_data = cities[city_key]
        result = {"city": city_key, "approx": True, "prices": {}}

        transport_lower = (transport_type or "").casefold()

        # Filter by transport_type if specified
        transport_keys = ["auto_rickshaw", "taxi_app", "taxi", "taxi_yellow", "metro",
                          "local_train", "tram", "boat_ride", "scooter_rental", "shared_jeep"]
        for key in transport_keys:
            if key in city_data:
                if not transport_lower or any(t in key for t in transport_lower.split()):
                    result["prices"][key] = city_data[key]
        result["prices"]["meals"] = city_data.get("meals", {})

        result["source"] = data.get("source_name", "")
        result["source_url"] = data.get("source_url", "")
        result["last_verified"] = data.get("last_verified", "2024-10")
        result["disclaimer"] = data.get("disclaimer", "All prices are approximate.")
        if context:
            result["context"] = context

        return result
    except Exception as exc:
        return {"error": f"Fair price lookup failed: {exc}"}


def atm_info(city: str = "") -> dict:
    """Return ATM and cash withdrawal guidance for a city.

    Args:
        city: Optional city name for city-specific tips.

    Returns:
        dict with ATM guidance and tips.
    """
    try:
        city = str(city or "").strip()
        general = _ATM_INFO["general"]
        city_lower = city.casefold()
        specific = _ATM_INFO["per_city"].get(city_lower, "")

        return {
            "general_atm_info": general,
            "city_specific": specific if specific else "No city-specific ATM notes available; general guidance applies.",
            "city": city or "general",
            "tip": "Always notify your bank before international travel to avoid card blocks.",
            "emergency_cash": "If stuck without cash: hotel front desks may assist; Western Union and MoneyGram outlets are available in major cities.",
        }
    except Exception as exc:
        return {"error": f"ATM info lookup failed: {exc}"}
