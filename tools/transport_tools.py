"""Grounded route and local-transport helpers for Batch B7."""

import hashlib
import json
import logging
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import TAVILY_API_KEY
from tools.maps_tool import distance_and_time, nearby_places_by_type


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = PROJECT_ROOT / "data" / "cache" / "transport_cache.sqlite3"
logger = logging.getLogger(__name__)
_CACHE_TTL_SECONDS = 24 * 60 * 60


def _cache_connection():
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_PATH), timeout=5)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS route_cache "
        "(cache_key TEXT PRIMARY KEY, response_json TEXT NOT NULL, created_at REAL NOT NULL)"
    )
    return conn


def _cache_key(origin, destination):
    value = f"{origin.strip().casefold()}|{destination.strip().casefold()}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _cache_get(origin, destination):
    try:
        with _cache_connection() as conn:
            row = conn.execute(
                "SELECT response_json, created_at FROM route_cache WHERE cache_key = ?",
                (_cache_key(origin, destination),),
            ).fetchone()
            if row and time.time() - row[1] < _CACHE_TTL_SECONDS:
                logger.info("transport cache hit: %s -> %s", origin, destination)
                return json.loads(row[0])
            if row:
                conn.execute("DELETE FROM route_cache WHERE cache_key = ?", (_cache_key(origin, destination),))
    except Exception as exc:
        logger.warning("transport cache read failed: %s", exc)
    return None


def _cache_set(origin, destination, result):
    try:
        with _cache_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO route_cache VALUES (?, ?, ?)",
                (_cache_key(origin, destination), json.dumps(result, ensure_ascii=False), time.time()),
            )
    except Exception as exc:
        logger.warning("transport cache write failed: %s", exc)


def _web_search(query, limit=4):
    if not TAVILY_API_KEY:
        return []
    try:
        from tavily import TavilyClient

        response = TavilyClient(api_key=TAVILY_API_KEY).search(
            query=query, search_depth="basic", max_results=limit
        )
        return [
            {
                "title": str(item.get("title") or "Travel information"),
                "content": str(item.get("content") or ""),
                "url": str(item.get("url") or ""),
            }
            for item in response.get("results", [])
            if item.get("content")
        ]
    except Exception as exc:
        logger.warning("transport web search failed: %s", exc)
        return []


def _kb_records(query, category, place=None):
    try:
        from agents.rag_agent import retrieve

        return retrieve(query, n_results=5, place=place, category=category).get("records", [])
    except Exception as exc:
        logger.warning("transport KB lookup failed: %s", exc)
        return []


def _nearest_facilities(destination):
    result = {"airport": "verify", "railway_station": "verify"}
    for key, place_type in (("airport", "airport"), ("railway_station", "train_station")):
        try:
            found = nearby_places_by_type(destination, place_type, radius_m=50000, limit=1)
            if found:
                result[key] = found[0].get("name") or "verify"
        except Exception:
            pass
    return result


def _safe_text(value, max_len=600):
    text = re.sub(r"https?://\S+", "", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _route_response(origin, destination):
    road = {}
    try:
        road = distance_and_time(origin, destination, mode="driving") or {}
    except Exception:
        road = {}

    search_results = _web_search(
        f"{origin} to {destination} train bus flight travel duration approximate fare route information",
        limit=5,
    )
    route_records = _kb_records(
        f"How to reach {destination} from {origin}; airports and railway stations",
        "how_to_reach",
        place=destination,
    )
    facilities = _nearest_facilities(destination)

    rows = []
    rows.append({
        "mode": "Road",
        "duration": road.get("duration_text") or "verify",
        "distance": road.get("distance_text") or "verify",
        "approx_cost": "verify",
        "notes": "Google Maps driving route" if road else "Google Maps route unavailable; verify distance and duration.",
        "source": "Google Maps Distance Matrix" if road else "",
    })

    for mode in ("Train", "Bus", "Flight"):
        terms = {"Train": r"train|rail|railway", "Bus": r"bus|coach", "Flight": r"flight|airline|airport"}
        matching = [item for item in search_results if re.search(terms[mode], item["title"] + " " + item["content"], re.I)]
        selected = matching[0] if matching else None
        if selected:
            content = _safe_text(selected["content"])
            time_match = re.search(r"\b\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?|days?)\b", content, re.I)
            money_match = re.search(r"(?:INR|Rs\.?|₹)\s*[\d,]+(?:\s*[-–]\s*(?:INR|Rs\.?|₹)?\s*[\d,]+)?", content, re.I)
            duration = time_match.group(0) if time_match else "verify"
            cost = f"approx {money_match.group(0)}; verify current fare" if money_match else "verify"
            note = content or "Check current operator information."
            source = selected["title"]
        else:
            duration, cost, note, source = "verify", "verify", "No current route data found; verify with the operator.", ""
        rows.append({
            "mode": mode,
            "duration": duration,
            "distance": "verify",
            "approx_cost": cost,
            "notes": note,
            "source": source,
        })

    airport = facilities["airport"]
    railway = facilities["railway_station"]
    if route_records:
        for record in route_records:
            text = record.get("text", "")
            if airport == "verify":
                match = re.search(r"(?:served by|airport(?:s)? (?:is|are|include|links?))\s+([^.;]+)", text, re.I)
                if match:
                    airport = _safe_text(match.group(1), 150)
            if railway == "verify":
                match = re.search(r"([^.;]+(?:railway|rail|junction|station)[^.;]*)", text, re.I)
                if match:
                    railway = _safe_text(match.group(1), 150)

    sources = [
        {"source_name": record.get("source_name", ""), "source_url": record.get("source_url", "")}
        for record in route_records
        if record.get("source_name") and record.get("source_url")
    ]
    sources.extend(
        {"source_name": item["title"], "source_url": ""}
        for item in search_results
        if item.get("title") and not re.search(r"book|booking|payment|checkout", item.get("url", ""), re.I)
    )
    sources = list({(item["source_name"], item["source_url"]): item for item in sources}.values())
    result = {
        "origin": origin,
        "destination": destination,
        "rows": rows,
        "nearest_airport": airport,
        "nearest_railway_station": railway,
        "recommendation": (
            "Compare the verified duration and distance above; select a mode only after checking current schedules and fares."
        ),
        "verify_line": "Verify schedules and fares on IRCTC or the relevant airline/operator site before travel. No booking links are provided.",
        "sources": sources,
    }

    result["markdown"] = _route_markdown(result)
    result["ui"] = {
        "type": "route_options",
        "version": "1.0",
        "data": {
            "origin": origin,
            "destination": destination,
            "options": rows,
            "nearest_airport": airport,
            "nearest_railway_station": railway,
            "recommendation": result["recommendation"],
            "verify_line": result["verify_line"],
            "sources": result["sources"],
        }
    }
    return result



def _route_markdown(result):
    lines = [
        f"| Mode | Duration | Distance | Approx cost | Notes |",
        "|---|---|---|---|---|",
    ]
    for row in result["rows"]:
        note = _safe_text(row["notes"], 180).replace("|", "/")
        if row.get("source"):
            note += f" (Source: {_safe_text(row['source'], 80)})"
        lines.append(
            f"| {row['mode']} | {row['duration']} | {row['distance']} | {row['approx_cost']} | {note} |"
        )
    lines.extend([
        "",
        f"Nearest airport: {result['nearest_airport']}",
        f"Nearest railway station: {result['nearest_railway_station']}",
        f"Recommendation: {result['recommendation']}",
        result["verify_line"],
    ])
    return "\n".join(lines)


def how_to_reach(origin, destination):
    """Return sourced route options; missing measurements are explicitly marked verify."""
    try:
        origin = str(origin or "").strip()
        destination = str(destination or "").strip()
        if not origin or not destination:
            return {"error": "origin and destination are required"}
        cached = _cache_get(origin, destination)
        if cached is not None:
            cached["cache"] = "hit"
            return cached
        result = _route_response(origin, destination)
        result["cache"] = "miss"
        _cache_set(origin, destination, result)
        return result
    except Exception as exc:
        return {"error": f"Route lookup unavailable: {exc}"}


def _rank_transport(record):
    text = (record.get("text") or "").lower()
    if "metro" in text:
        rank = 1
    elif "ferry" in text or "water metro" in text or "boat" in text:
        rank = 2
    elif "bus" in text:
        rank = 3
    elif "train" in text or "rail" in text:
        rank = 4
    elif "auto" in text or "rickshaw" in text:
        rank = 5
    elif "taxi" in text or "cab" in text:
        rank = 6
    else:
        rank = 7
    return rank


def _transport_option(record):
    text = _safe_text(record.get("text", ""))
    fare = "verify current fare"
    fare_match = re.search(
        r"(?:approx\s*)?(?:Rs\.?|INR|₹)\s*[\d,]+(?:\s*(?:to|-|–)\s*(?:Rs\.?|INR|₹)?\s*[\d,]+)?(?:\s*(?:per\s*[\w-]+|for\s*[\w-]+))?",
        text,
        re.I,
    )
    if fare_match:
        fare_text = fare_match.group(0)
        if not re.match(r"(?i)^approx\b", fare_text):
            fare_text = f"approx {fare_text}"
        fare = f"{fare_text}; verify current fare"
    tags = record.get("tags", [])
    lowered = text.lower()
    if not tags:
        for keyword, tag in (
            ("water metro", "water_metro"), ("metro", "metro"), ("ferr", "ferry"),
            ("bus", "bus"), ("auto", "auto"), ("rickshaw", "rickshaw"),
            ("taxi", "taxi"), ("cab", "cab"),
        ):
            if keyword in lowered:
                tags.append(tag)
    return {
        "mode": next((tag.replace("_", " ").title() for tag in tags if tag in {
            "metro", "water_metro", "ferry", "bus", "auto", "cab", "rickshaw", "taxi"
        }), "Local transit"),
        "fare_range": fare,
        "comfort": "Depends on route and service conditions; verify locally.",
        "tips": text,
        "source_name": record.get("source_name", ""),
        "source_url": record.get("source_url", ""),
    }


def get_local_transport(city):
    """Return ranked local options from KB, falling back to web snippets; never raises."""
    try:
        city = str(city or "").strip()
        if not city:
            return {"error": "city is required"}
        records = _kb_records(f"Local transport in {city}: metro, buses, ferries, autos and fares", "local_transport", place=city)
        options = []
        for record in records:
            option = _transport_option(record)
            if option["tips"] and option not in options:
                options.append(option)

        sources = []
        if options:
            sources = list(dict.fromkeys(option["source_name"] for option in options if option["source_name"]))
        else:
            for item in _web_search(f"official local transport guide {city} buses metro ferry auto fares", limit=5):
                content = _safe_text(item["content"])
                if not content:
                    continue
                pseudo_record = {
                    "text": content,
                    "tags": [],
                    "source_name": item["title"],
                    "source_url": item["url"] if "book" not in item["url"].lower() else "",
                }
                options.append(_transport_option(pseudo_record))
                sources.append(item["title"])
        options.sort(key=lambda option: _rank_transport({"text": option["tips"]}))
        options = options[:6]
        markdown = "| Rank | Option | Approx fare range | Comfort | Tips |\n|---:|---|---|---|---|"
        for index, option in enumerate(options, 1):
            markdown += (
                f"\n| {index} | {option['mode']} | {option['fare_range']} | "
                f"{option['comfort']} | {_safe_text(option['tips'], 220).replace('|', '/')} |"
            )
        if not options:
            markdown += "\n| - | No verified local options found | verify current fare | verify | Check official local transport information. |"
        return {
            "city": city,
            "options": options,
            "recommendation": "Prefer metro/rail or official public buses where they serve your route; confirm today's route and fare before departure.",
            "markdown": markdown + "\n\nAll fares are approximate where stated; otherwise verify current fare locally.",
            "sources": list(dict.fromkeys(sources)),
            "grounded": bool(options),
        }
    except Exception as exc:
        return {"error": f"Local transport lookup unavailable: {exc}"}
