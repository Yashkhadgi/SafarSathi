"""Deterministic, explicitly approximate trip budget estimates."""

import json
import math
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_PATH = PROJECT_ROOT / "data" / "budget" / "cost_benchmarks.json"
TIERS = ("backpacker", "mid", "luxury")
TIER_LABELS = {"backpacker": "Backpacker", "mid": "Mid-range", "luxury": "Luxury"}


def _benchmarks():
    with BENCHMARK_PATH.open(encoding="utf-8") as source:
        return json.load(source)


def _number(value, name, minimum=0):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise ValueError(f"{name} must be a finite number >= {minimum}")
    return int(round(result))


def _tier(value):
    normalized = str(value or "mid").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {"mid_range": "mid", "middle": "mid", "budget": "backpacker", "luxury": "luxury"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in TIERS:
        raise ValueError("tier must be backpacker, mid, or luxury")
    return normalized


def _city_names(trip, benchmarks):
    requested = []
    for key in ("destination", "destinations", "city", "cities"):
        value = trip.get(key)
        if isinstance(value, str):
            requested.append(value)
        elif isinstance(value, (list, tuple)):
            requested.extend(str(item) for item in value)
    for day in trip.get("days", []) if isinstance(trip.get("days"), list) else []:
        if isinstance(day, dict):
            for slot in day.get("slots", []) or []:
                if isinstance(slot, dict) and slot.get("place"):
                    requested.append(str(slot["place"]))
    found = []
    for city in benchmarks["cities"]:
        if any(re.search(rf"(?<!\w){re.escape(city)}(?!\w)", value, re.I) for value in requested):
            if city not in found:
                found.append(city)
    return found


def _trip_days(trip):
    days = trip.get("days")
    if isinstance(days, list):
        return len(days)
    for key in ("duration_days", "num_days", "days"):
        value = trip.get(key)
        if value is not None and not isinstance(value, (list, dict)):
            return _number(value, "days", minimum=1)
    raise ValueError("trip must include days or duration_days")


def _entry_override(trip):
    if trip.get("entry_fees_inr") is not None:
        return _number(trip["entry_fees_inr"], "entry_fees_inr")
    days = trip.get("days")
    if not isinstance(days, list):
        return None
    per_person = 0
    any_values = False
    for day in days:
        for slot in day.get("slots", []) if isinstance(day, dict) else []:
            if isinstance(slot, dict) and slot.get("cost_est_inr") is not None:
                per_person += _number(slot["cost_est_inr"], "slot cost_est_inr")
                any_values = True
    return per_person if any_values else None


def _build_estimate(trip, travelers, tier, currency="INR"):
    if not isinstance(trip, dict):
        raise ValueError("trip must be a dictionary")
    travelers = _number(travelers, "travelers", minimum=1)
    days = _trip_days(trip)
    tier = _tier(tier)
    data = _benchmarks()
    cities = _city_names(trip, data)
    if not cities:
        raise ValueError("trip destination must match a city in the current knowledge base")

    city_data = [data["cities"][city] for city in cities]
    city_factors = [float(city["multiplier"]) for city in city_data]
    city_multiplier = sum(city_factors) / len(city_factors)
    daily = {
        category: round(sum(city["daily_per_person_inr"][tier][category] for city in city_data) / len(city_data))
        for category in ("food", "local_transport", "entry_fees", "shopping")
    }
    stay_rates = {
        key: round(sum(city["stay_per_night_inr"][key] for city in city_data) / len(city_data))
        for key in ("backpacker_bed", "mid_room", "luxury_room")
    }
    if tier == "backpacker":
        stay_rate = stay_rates["backpacker_bed"]
        rooms = travelers
    else:
        stay_rate = stay_rates[f"{tier}_room"]
        rooms = _number(trip.get("rooms", math.ceil(travelers / 2)), "rooms", minimum=1)
    nights = max(0, days - 1)
    stay_total = stay_rate * rooms * nights

    food_total = daily["food"] * travelers * days
    local_total = daily["local_transport"] * travelers * days
    entry_override = _entry_override(trip)
    if entry_override is None:
        entry_total = daily["entry_fees"] * travelers * days
        entry_note = "Daily per-person entry-fee guess used."
    else:
        entry_total = entry_override * travelers
        entry_note = "Itinerary cost_est_inr values treated as per-person entry estimates."

    supplied_transport = trip.get("transport_to_destination_inr")
    supplied_transport_per_person = trip.get("transport_to_destination_per_person_inr")
    if supplied_transport is not None:
        transport_total = _number(supplied_transport, "transport_to_destination_inr")
        transport_note = "User-supplied total for the group."
    elif supplied_transport_per_person is not None:
        transport_total = _number(supplied_transport_per_person, "transport_to_destination_per_person_inr") * travelers
        transport_note = "User-supplied per-person amount multiplied by travelers."
    else:
        transport_total = 0
        transport_note = "Not included: origin/route fare was not supplied; verify separately."

    shopping_total = daily["shopping"] * travelers * days
    subtotal = transport_total + stay_total + food_total + local_total + entry_total + shopping_total
    buffer_rate = float(data.get("buffer_rate", 0.12))
    if not 0.10 <= buffer_rate <= 0.15:
        raise ValueError("benchmark buffer_rate must be between 10% and 15%")
    buffer_total = round(subtotal * buffer_rate)
    categories = {
        "transport_to_destination": transport_total,
        "stay": stay_total,
        "food": food_total,
        "local_transport": local_total,
        "entry_fees": entry_total,
        "shopping": shopping_total,
        "buffer": buffer_total,
    }
    total = subtotal + buffer_total
    assert sum(categories.values()) == total, "budget category sum mismatch"

    source = data["source"]
    city_sources = [city["source"] for city in city_data]
    last_verified = max(city["last_verified"] for city in city_data)
    assumptions = [
        "Approximate planning estimate; city-level values are guesses, not current quotes.",
        f"Average city multiplier for {', '.join(cities)} is {city_multiplier:.2f}x; city-specific figures are unverified estimates.",
        f"Stay uses {rooms} {'dorm bed(s)' if tier == 'backpacker' else 'room(s)'} for {nights} night(s).",
        transport_note,
        entry_note,
        f"A {buffer_rate:.0%} contingency buffer is included.",
        "Flights to/from the destination, insurance, taxes, and child-specific rates are excluded unless supplied.",
    ]

    result = {
        "currency": "INR",
        "destination": cities,
        "days": days,
        "travelers": travelers,
        "tier": tier,
        "categories": categories,
        "total_inr": total,
        "per_person_inr": round(total / travelers),
        "per_person_per_day_inr": round(total / (travelers * days)),
        "buffer_rate": buffer_rate,
        "confidence": "guess",
        "approx": True,
        "last_verified": last_verified,
        "source": source,
        "city_sources": city_sources,
        "assumptions": assumptions,
        "markdown": _format_markdown(categories, total, travelers, days, tier, source, entry_note, transport_note),
    }

    currency = str(currency or "INR").strip().upper()
    if currency != "INR":
        try:
            from tools.currency_tool import convert_currency

            converted = convert_currency(total, "INR", currency)
            if isinstance(converted, dict) and not converted.get("error"):
                result["converted_total"] = {
                    "currency": currency,
                    "amount": converted.get("converted_amount"),
                    "rate": converted.get("rate"),
                    "approx": True,
                }
            else:
                result["currency_conversion"] = "Unavailable; estimate remains in INR."
        except Exception:
            result["currency_conversion"] = "Unavailable; estimate remains in INR."
    return result


def _format_markdown(categories, total, travelers, days, tier, source, entry_note, transport_note):
    labels = {
        "transport_to_destination": "Transport to destination",
        "stay": "Stay",
        "food": "Food",
        "local_transport": "Local transport",
        "entry_fees": "Entry fees",
        "shopping": "Shopping",
        "buffer": "12% buffer",
    }
    lines = ["| Category | Approx total (INR) | Notes |", "|---|---:|---|"]
    for category, amount in categories.items():
        note = transport_note if category == "transport_to_destination" else (
            entry_note if category == "entry_fees" else "Approximate estimate; verify current rates."
        )
        lines.append(f"| {labels[category]} | {amount:,} | {note} |")
    lines.extend([
        f"| **Total ({TIER_LABELS[tier]})** | **{total:,}** | Approx; last verified {source['accessed']} |",
        f"| Per person | {round(total / travelers):,} | {travelers} traveler(s) |",
        f"| Per person per day | {round(total / (travelers * days)):,} | {days} day(s) |",
        "",
        f"Source baseline: [{source['name']}]({source['url']}); city allocation is a guess.",
    ])
    return "\n".join(lines)


def estimate_budget(trip, travelers, tier, currency="INR"):
    """Estimate a budget with Python arithmetic. Returns a result or an error object."""
    try:
        return _build_estimate(trip, travelers, tier, currency=currency)
    except Exception as exc:
        return {"error": f"Could not estimate budget: {exc}"}


def compare_budget_tiers(trip, travelers, currency="INR"):
    """Estimate the same trip in all three tiers and return a comparison table."""
    try:
        estimates = [_build_estimate(trip, travelers, tier, currency="INR") for tier in TIERS]
        if currency and str(currency).upper() != "INR":
            estimates = [_build_estimate(trip, travelers, tier, currency=currency) for tier in TIERS]
        lines = [
            "| Tier | Approx total (INR) | Per person | Per person/day | Stay | Transport | Food |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for estimate in estimates:
            categories = estimate["categories"]
            lines.append(
                f"| {TIER_LABELS[estimate['tier']]} | {estimate['total_inr']:,} | "
                f"{estimate['per_person_inr']:,} | {estimate['per_person_per_day_inr']:,} | "
                f"{categories['stay']:,} | {categories['transport_to_destination'] + categories['local_transport']:,} | "
                f"{categories['food']:,} |"
            )
        result = {
            "estimates": estimates,
            "markdown": "\n".join(lines),
            "recommendation": (
                "Backpacker minimizes spend; mid-range is the balanced comfort option; luxury increases stay, dining, and transport allowances. "
                "These are guesses, so compare current provider prices before booking."
            ),
            "assumptions": list(estimates[0]["assumptions"]),
            "approx": True,
            "last_verified": estimates[0]["last_verified"],
        }
        return result
    except Exception as exc:
        return {"error": f"Could not compare budget tiers: {exc}"}
