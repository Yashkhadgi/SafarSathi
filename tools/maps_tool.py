import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import googlemaps
import math
from config.settings import GOOGLE_MAPS_API_KEY

_gmaps = None


def _client():
    global _gmaps
    if _gmaps is None:
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("GOOGLE_MAPS_API_KEY not set in .env")
        _gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    return _gmaps


def _nearby_attractions_uncached(place_name: str, radius_m: int = 5000, limit: int = 5):
    try:
        gmaps = _client()
        geocode = gmaps.geocode(place_name)
        if not geocode:
            return []
        location = geocode[0]["geometry"]["location"]

        results = gmaps.places_nearby(
            location=location, radius=radius_m, type="tourist_attraction"
        )
        attractions = []
        for r in results.get("results", [])[:limit]:
            attractions.append({
                "name": r.get("name"),
                "address": r.get("vicinity"),
                "rating": r.get("rating"),
            })
        return attractions
    except Exception as e:
        print(f"Maps lookup failed: {e}")
        return []


def nearby_attractions(place_name: str, radius_m: int = 5000, limit: int = 5):
    from memory.cache import cached_call

    return cached_call("maps_attractions", [place_name, radius_m, limit], 3600,
                       lambda: _nearby_attractions_uncached(place_name, radius_m, limit))


def _distance_and_time_uncached(origin: str, destination: str, mode: str = "driving"):
    try:
        gmaps = _client()
        result = gmaps.distance_matrix(origins=[origin], destinations=[destination], mode=mode)
        element = result["rows"][0]["elements"][0]
        if element["status"] != "OK":
            return {}
        return {
            "distance_text": element["distance"]["text"],
            "duration_text": element["duration"]["text"],
        }
    except Exception as e:
        print(f"Distance lookup failed: {e}")
        return {}


def distance_and_time(origin: str, destination: str, mode: str = "driving"):
    from memory.cache import cached_call

    return cached_call("maps_route", [origin, destination, mode], 24 * 3600,
                       lambda: _distance_and_time_uncached(origin, destination, mode))


def _nearby_places_by_type_uncached(place_name: str, place_type: str, radius_m: int = 5000, limit: int = 3):
    try:
        gmaps = _client()
        geocode = gmaps.geocode(place_name)
        if not geocode:
            return []
        location = geocode[0]["geometry"]["location"]
        results = gmaps.places_nearby(location=location, radius=radius_m, type=place_type)
        places = []
        for r in results.get("results", [])[:limit]:
            places.append({
                "name": r.get("name"),
                "address": r.get("vicinity"),
                "rating": r.get("rating"),
            })
        return places
    except Exception as e:
        print(f"Nearby {place_type} lookup failed: {e}")
        return []


def nearby_places_by_type(place_name: str, place_type: str, radius_m: int = 5000, limit: int = 3):
    from memory.cache import cached_call

    return cached_call("maps_nearby", [place_name, place_type, radius_m, limit], 3600,
                       lambda: _nearby_places_by_type_uncached(place_name, place_type, radius_m, limit))


def nearest_emergency_services(city: str = "", latitude=None, longitude=None):
    """Return nearest listed hospital and police place; failures return empty results."""
    try:
        gmaps = _client()
        if latitude is not None and longitude is not None:
            center = {"lat": float(latitude), "lng": float(longitude)}
        elif city and str(city).strip():
            geocoded = gmaps.geocode(str(city).strip())
            if not geocoded:
                return {"hospitals": [], "police": []}
            center = geocoded[0]["geometry"]["location"]
        else:
            return {"hospitals": [], "police": []}

        def distance_m(location):
            lat1, lon1 = math.radians(center["lat"]), math.radians(center["lng"])
            lat2, lon2 = math.radians(location["lat"]), math.radians(location["lng"])
            dlat, dlon = lat2 - lat1, lon2 - lon1
            value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            return 6371000 * 2 * math.atan2(math.sqrt(value), math.sqrt(max(0.0, 1 - value)))

        output = {}
        for label, place_type in (("hospitals", "hospital"), ("police", "police")):
            response = gmaps.places_nearby(location=center, radius=5000, type=place_type)
            places = []
            for item in response.get("results", []):
                geometry = item.get("geometry", {}).get("location")
                if not geometry:
                    continue
                places.append({
                    "name": item.get("name", "Nearby service"),
                    "address": item.get("vicinity", ""),
                    "distance_m": round(distance_m(geometry)),
                })
            output[label] = sorted(places, key=lambda item: item["distance_m"])[:3]
        return output
    except Exception as e:
        print(f"Emergency place lookup failed: {e}")
        return {"hospitals": [], "police": []}


def get_place_coordinates(place_name: str):
    """Geocode a user-entered place; failures return an empty mapping."""
    try:
        results = _client().geocode(str(place_name or "").strip())
        if not results:
            return {}
        location = results[0].get("geometry", {}).get("location", {})
        lat, lng = float(location["lat"]), float(location["lng"])
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return {}
        return {"latitude": lat, "longitude": lng}
    except Exception as e:
        print(f"Geocoding failed: {e}")
        return {}


if __name__ == "__main__":
    print(nearby_attractions("Udaipur"))
    print(distance_and_time("Jaipur", "Udaipur"))
