"""Key-free itinerary map using OpenStreetMap data and a sandboxed Leaflet frame."""

import html
import json
import threading
import time

import requests

from memory.cache import cached_call


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_POLICY = "https://operations.osmfoundation.org/policies/nominatim/"
_geocode_lock = threading.Lock()
_last_request = 0.0
_colors = ["#167d83", "#d94f35", "#8557a3", "#ce9e28", "#34814b", "#bf5d83"]


def _geocode_osm(query):
    global _last_request
    with _geocode_lock:
        wait = 1.05 - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        response = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "in"},
            headers={"User-Agent": "SafarSathi/1.1 (local itinerary map)"},
            timeout=10,
        )
    response.raise_for_status()
    results = response.json()
    if not results:
        return {"error": "Place not found on OpenStreetMap"}
    return {"lat": float(results[0]["lat"]), "lng": float(results[0]["lon"]),
            "label": results[0].get("display_name", query),
            "source_url": f"https://www.openstreetmap.org/{results[0]['osm_type']}/{results[0]['osm_id']}"}


def geocode_osm(query):
    try:
        if not str(query or "").strip():
            return {"error": "Place required"}
        return cached_call("osm_geocode", [query], 7 * 24 * 3600,
                           lambda: _geocode_osm(query))
    except Exception as exc:
        return {"error": f"OpenStreetMap lookup unavailable: {exc}"}


def map_points(trip):
    """Only use OSM positions or explicitly OSM-sourced coordinates on an OSM map."""
    points, missing = [], []
    destination = str(trip.get("destination", "")).strip()
    for day in trip.get("days", []):
        for slot in day.get("slots", []):
            name = str(slot.get("place", "")).strip()
            if not name:
                continue
            coords = slot.get("map_coordinates") or {}
            if coords.get("source") != "OpenStreetMap":
                coords = geocode_osm(f"{name}, {destination}, India")
            if "error" in coords or not {"lat", "lng"} <= coords.keys():
                missing.append(name)
                continue
            points.append({"name": name, "day": day.get("day", 1),
                           "time": slot.get("time", "verify"),
                           "lat": float(coords["lat"]), "lng": float(coords["lng"])})
    return {"points": points, "missing": missing, "source_url": NOMINATIM_POLICY}


def render_map_html(points, selected_day="all"):
    """Render a map without injecting untrusted trip text as executable JavaScript."""
    try:
        selected = str(selected_day or "all")
        visible = [point for point in points if selected == "all" or
                   str(point.get("day")) == selected]
        if not visible:
            return "<p>No mapped stops for this day.</p>"
        payload = json.dumps(visible, ensure_ascii=False).replace("<", "\\u003c")
        colors = json.dumps(_colors)
        document = f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>html,body,#map{{height:100%;margin:0}} .leaflet-popup-content{{font:14px system-ui;line-height:1.4}}</style>
</head><body><div id="map"></div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const points = {payload}; const colors = {colors};
const map = L.map('map', {{scrollWheelZoom:false}});
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
}}).addTo(map);
const bounds = [];
for (const point of points) {{
  const color = colors[(Number(point.day)-1) % colors.length];
  const marker = L.circleMarker([point.lat,point.lng], {{radius:8,color,weight:2,fillColor:color,fillOpacity:.85}}).addTo(map);
  const popup = document.createElement('div');
  const title = document.createElement('strong'); title.textContent = point.name;
  const detail = document.createElement('div'); detail.textContent = 'Day ' + point.day + ' | ' + point.time;
  popup.append(title,detail); marker.bindPopup(popup); bounds.push([point.lat,point.lng]);
}}
for (const day of [...new Set(points.map(p => Number(p.day)))]) {{
  const route = points.filter(p => Number(p.day) === day).map(p => [p.lat,p.lng]);
  if (route.length > 1) L.polyline(route, {{color:colors[(day-1)%colors.length],weight:3,opacity:.8}}).addTo(map);
}}
map.fitBounds(bounds, {{padding:[30,30],maxZoom:14}});
</script></body></html>"""
        return ("<iframe title='Itinerary map' sandbox='allow-scripts' loading='lazy' "
                "style='width:100%;height:520px;border:0;max-width:100%' "
                f"srcdoc=\"{html.escape(document, quote=True)}\"></iframe>")
    except Exception as exc:
        return f"<p>Map unavailable: {html.escape(str(exc))}</p>"


def trip_map(trip, selected_day="all"):
    try:
        positions = map_points(trip)
        return {"html": render_map_html(positions["points"], selected_day),
                "missing": positions["missing"], "mapped": len(positions["points"]),
                "source_url": positions["source_url"]}
    except Exception as exc:
        return {"error": f"Map unavailable: {exc}"}
