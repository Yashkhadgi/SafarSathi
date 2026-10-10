import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import googlemaps
from config.settings import GOOGLE_MAPS_API_KEY

_gmaps = None


def _client():
    global _gmaps
    if _gmaps is None:
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("GOOGLE_MAPS_API_KEY not set in .env")
        _gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    return _gmaps


def nearby_attractions(place_name: str, radius_m: int = 5000, limit: int = 5):
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


def distance_and_time(origin: str, destination: str, mode: str = "driving"):
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


def nearby_places_by_type(place_name: str, place_type: str, radius_m: int = 5000, limit: int = 3):
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


if __name__ == "__main__":
    print(nearby_attractions("Udaipur"))
    print(distance_and_time("Jaipur", "Udaipur"))
