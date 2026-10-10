"""Live weather, opening-hours, and consented nearby lookup."""

import math
from datetime import date, datetime, timezone

import requests

from config.settings import GOOGLE_MAPS_API_KEY, OPENWEATHER_API_KEY
from memory.cache import cached_call


OPENWEATHER_DOC = "https://openweathermap.org/api/air-pollution"
GOOGLE_PLACES_DOC = "https://developers.google.com/maps/documentation/places/web-service/legacy/details"
AIR_LABELS = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very poor"}
NEARBY_TYPES = {
    "attractions": "tourist_attraction", "restaurants": "restaurant",
    "atm": "atm", "restrooms": "public_bathroom", "petrol": "gas_station",
    "pharmacy": "pharmacy",
}


def air_quality_advice(aqi, scale="openweather"):
    """Keep the provider's 1-5 scale distinct from a 0-500 AQI scale."""
    try:
        value = float(aqi)
        if scale == "openweather":
            return "Poor air quality; consider reducing prolonged outdoor activity." if value >= 4 else ""
        if scale == "us" and value >= 300:
            return "Hazardous AQI; limit outdoor activity and follow local health advice."
        return ""
    except (TypeError, ValueError):
        return ""


def _get_live_weather(place, days):
    forecast_resp = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"q": place, "appid": OPENWEATHER_API_KEY, "units": "metric"}, timeout=10,
    )
    forecast_resp.raise_for_status()
    forecast_data = forecast_resp.json()
    forecast = []
    by_day = {}
    for item in forecast_data.get("list", []):
        day = item.get("dt_txt", "")[:10]
        if not day:
            continue
        bucket = by_day.setdefault(day, {"temps": [], "conditions": []})
        bucket["temps"].append(float(item["main"]["temp"]))
        bucket["conditions"].append(item["weather"][0]["description"])
    for day, item in list(by_day.items())[:days]:
        forecast.append({"date": day, "temp_min": round(min(item["temps"]), 1),
                         "temp_max": round(max(item["temps"]), 1),
                         "condition": item["conditions"][0]})
    if not forecast:
        return {"error": "Live forecast unavailable"}

    current_resp = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": place, "appid": OPENWEATHER_API_KEY, "units": "metric"}, timeout=10,
    )
    current_resp.raise_for_status()
    current_data = current_resp.json()
    coord = current_data.get("coord", {})
    current = {"temp_c": current_data.get("main", {}).get("temp"),
               "condition": current_data.get("weather", [{}])[0].get("description", "verify")}
    warnings = []
    if current["temp_c"] is not None and float(current["temp_c"]) >= 40:
        warnings.append("High heat; consider limiting midday outdoor activity.")
    if "rain" in current["condition"].casefold():
        warnings.append("Rain reported; verify outdoor plans.")
    air = {"error": "AQI unavailable"}
    if "lat" in coord and "lon" in coord:
        try:
            air_resp = requests.get(
                "https://api.openweathermap.org/data/2.5/air_pollution",
                params={"lat": coord["lat"], "lon": coord["lon"],
                        "appid": OPENWEATHER_API_KEY}, timeout=10,
            )
            air_resp.raise_for_status()
            entry = air_resp.json().get("list", [])[0]
            level = int(entry["main"]["aqi"])
            air = {"index": level, "scale": "OpenWeather 1-5",
                   "label": AIR_LABELS.get(level, "verify"),
                   "pm2_5_ug_m3": entry.get("components", {}).get("pm2_5"),
                   "source_url": OPENWEATHER_DOC}
            advice = air_quality_advice(level)
            if advice:
                warnings.append(advice)
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
            pass
    verified = datetime.now(timezone.utc).date().isoformat()
    res = {"place": place, "current": current, "forecast": forecast, "air_quality": air,
           "warnings": warnings, "source_name": "OpenWeather",
           "source_url": OPENWEATHER_DOC, "last_verified": verified, "approx": True}
    res["ui"] = {
        "type": "weather",
        "version": "1.0",
        "data": {
            "city": place,
            "temperature_c": current.get("temp_c"),
            "condition": current.get("condition"),
            "air_quality": air,
            "forecast": forecast,
            "warnings": warnings,
            "last_verified": verified,
        }
    }
    return res


def get_live_weather(place, days=3):
    try:
        if not OPENWEATHER_API_KEY:
            return {"error": "Live weather and AQI unavailable; OPENWEATHER_API_KEY is not set"}
        days = int(days)
        if not 1 <= days <= 5:
            return {"error": "Forecast days must be 1-5"}
        return cached_call("live_weather_aqi", [place, days], 3600,
                           lambda: _get_live_weather(place, days))
    except Exception as exc:
        return {"error": f"Live weather unavailable: {exc}"}


def _opening_hours_live(place, city, visit_date):
    from tools.maps_tool import _client

    candidates = _client().places(query=f"{place}, {city}").get("results", [])
    if not candidates or not candidates[0].get("place_id"):
        return {"error": "Place details unavailable; verify opening hours"}
    details = _client().place(
        candidates[0]["place_id"],
        fields=["opening_hours", "current_opening_hours", "url", "name"],
    ).get("result", {})
    current = details.get("current_opening_hours", {})
    regular = details.get("opening_hours", {})
    dated = date.fromisoformat(visit_date)
    within_week = 0 <= (dated - datetime.now(timezone.utc).date()).days <= 6
    hours = current if within_week and current else regular
    weekday = dated.strftime("%A")
    weekday_text = next((text for text in hours.get("weekday_text", [])
                         if text.casefold().startswith(weekday.casefold() + ":")), "")
    special = any(day.get("date") == visit_date and day.get("exceptional_hours")
                  for day in current.get("special_days", [])) if within_week else False
    closed = "closed" in weekday_text.casefold() if weekday_text else None
    warnings = []
    if closed:
        warnings.append(f"{place} is listed closed on {weekday}; verify before visiting.")
    if special:
        warnings.append("Special or holiday hours may apply; verify on the official site.")
    if not weekday_text:
        warnings.append("Opening hours unavailable; verify before visiting.")
    return {"place": details.get("name", place), "visit_date": visit_date,
            "hours": weekday_text or "verify", "closed": closed, "warnings": warnings,
            "source_name": "Google Places", "source_url": details.get("url") or GOOGLE_PLACES_DOC,
            "last_verified": datetime.now(timezone.utc).date().isoformat(), "approx": True}


def get_opening_hours(place, city, visit_date):
    try:
        date.fromisoformat(visit_date)
        if not GOOGLE_MAPS_API_KEY:
            return {"error": "Live opening hours unavailable; verify with the venue"}
        return cached_call("opening_hours", [place, city, visit_date], 3600,
                           lambda: _opening_hours_live(place, city, visit_date))
    except Exception as exc:
        return {"error": f"Opening hours unavailable: {exc}"}


def _distance_km(a, b):
    lat1, lon1 = math.radians(a["lat"]), math.radians(a["lng"])
    lat2, lon2 = math.radians(b["lat"]), math.radians(b["lng"])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    square = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.atan2(math.sqrt(square), math.sqrt(max(0, 1 - square)))


def _near_me_live(latitude, longitude, kind, open_now, veg, min_rating):
    from tools.maps_tool import _client

    center = {"lat": float(latitude), "lng": float(longitude)}
    response = _client().places_nearby(
        location=center, radius=5000, type=NEARBY_TYPES[kind],
        open_now=bool(open_now),
    )
    results = []
    for item in response.get("results", []):
        position = item.get("geometry", {}).get("location")
        if not position or float(item.get("rating") or 0) < min_rating:
            continue
        if veg:
            if kind != "restaurants" or not item.get("place_id"):
                continue
            details = _client().place(item["place_id"], fields=["serves_vegetarian_food"])
            if details.get("result", {}).get("serves_vegetarian_food") is not True:
                continue
        results.append({"name": item.get("name", "Unnamed place"),
                        "distance_km": round(_distance_km(center, position), 2),
                        "rating": item.get("rating"),
                        "open_now": item.get("opening_hours", {}).get("open_now", "verify"),
                        "address": item.get("vicinity", ""), "latitude": position["lat"],
                        "longitude": position["lng"]})
    results.sort(key=lambda item: item["distance_km"])
    verified = datetime.now(timezone.utc).date().isoformat()
    res = {"results": results[:5], "source_name": "Google Places",
           "source_url": GOOGLE_PLACES_DOC,
           "last_verified": verified, "approx": True}
    res["ui"] = {
        "type": "near_me",
        "version": "1.0",
        "data": {
            "category": kind,
            "places": results[:5],
            "last_verified": verified,
        }
    }
    return res



def near_me(latitude=None, longitude=None, city="", kind="attractions", open_now=False,
            veg=False, min_rating=0, consent=False):
    try:
        if not consent:
            return {"error": "Location consent is required"}
        if not GOOGLE_MAPS_API_KEY:
            return {"error": "Nearby places unavailable; GOOGLE_MAPS_API_KEY is not set"}
        if kind not in NEARBY_TYPES or not 0 <= float(min_rating) <= 5:
            return {"error": "Invalid nearby filter"}
        if latitude is None or longitude is None:
            from tools.maps_tool import get_place_coordinates

            coordinates = get_place_coordinates(city)
            if not coordinates:
                return {"error": "Location unavailable; enter a city or allow browser location"}
            latitude, longitude = coordinates["latitude"], coordinates["longitude"]
        lat, lng = float(latitude), float(longitude)
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return {"error": "Invalid coordinates"}
        return cached_call("near_me", [round(lat, 4), round(lng, 4), kind,
                                       bool(open_now), bool(veg), float(min_rating)], 3600,
                           lambda: _near_me_live(lat, lng, kind, open_now, veg, float(min_rating)))
    except Exception as exc:
        return {"error": f"Nearby places unavailable: {exc}"}
