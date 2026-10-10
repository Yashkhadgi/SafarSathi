"""Source-grounded tourist scam guidance from the local knowledge base."""

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_PATH = PROJECT_ROOT / "data" / "knowledge_base"


def _key(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _records():
    records = []
    for path in KB_PATH.glob("*.json"):
        try:
            with path.open(encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                payload = [payload]
            if isinstance(payload, list):
                records.extend(row for row in payload if isinstance(row, dict))
        except (OSError, json.JSONDecodeError):
            continue
    return records


def known_scam_cities():
    try:
        return sorted({
            row.get("place", "") for row in _records()
            if row.get("category") == "scams" and row.get("place")
        })
    except Exception:
        return []


def get_scam_alerts(city, context=""):
    """Return 3-5 behavior-focused alerts; never raises on malformed or missing KB data."""
    try:
        city = str(city or "").strip()
        context = str(context or "").strip()
        if not city:
            return {"error": "city is required"}
        query = _key(city)
        candidates = [
            row for row in _records()
            if row.get("category") == "scams" and _key(row.get("place")) == query
        ]
        if not candidates:
            return {"error": f"No sourced scam alerts are available for {city}."}
        candidates.sort(key=lambda row: bool(row.get("alerts")), reverse=True)

        alerts = candidates[0].get("alerts", [])
        if not isinstance(alerts, list):
            alerts = []
        alerts = [item for item in alerts if isinstance(item, dict)]
        if not alerts:
            return {"error": f"No structured scam alerts are available for {city}."}

        context_key = _key(context)
        def relevance(alert):
            body = _key(" ".join(str(alert.get(field, "")) for field in ("situation", "how_to_avoid")))
            score = sum(1 for word in context_key.split() if len(word) > 3 and word in body)
            return score

        ordered = sorted(alerts, key=relevance, reverse=True)[:5]
        output = []
        for item in ordered:
            action = item.get("how_to_avoid", "Verify the provider and full price before agreeing.")
            sources = item.get("source", [])
            if isinstance(sources, dict):
                sources = [sources]
            source_rows = [
                {"source_name": str(source.get("name", "")), "source_url": str(source.get("url", ""))}
                for source in sources if isinstance(source, dict) and source.get("name") and source.get("url")
            ]
            alert = {
                "situation": str(item.get("situation", "")),
                "how_to_avoid": str(action),
                "what_to_do": str(action),
                "fair_price_hint": str(item.get("fair_price_hint", "No source-backed price verified; confirm before paying.")),
                "last_verified": str(item.get("last_verified", candidates[0].get("last_verified", ""))),
                "sources": source_rows,
            }
            output.append(alert)

        lines = [f"### Sourced scam and tourist-trap alerts for {candidates[0]['place']}"]
        for index, item in enumerate(output, start=1):
            source_links = "; ".join(f"[{source['source_name']}]({source['source_url']})" for source in item["sources"])
            lines.extend([
                f"{index}. **Situation:** {item['situation']}",
                f"   **What to do:** {item['what_to_do']}",
                f"   **Fair-price hint:** {item['fair_price_hint']} (last verified {item['last_verified']})",
                f"   **Sources:** {source_links or 'Source unavailable'}",
            ])
        return {"city": candidates[0]["place"], "alerts": output, "markdown": "\n\n".join(lines)}
    except Exception as exc:
        return {"error": f"Could not retrieve scam alerts: {exc}"}
