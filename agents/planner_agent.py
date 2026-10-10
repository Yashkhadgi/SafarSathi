import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.llm_wrapper import call_llm
from tools.maps_tool import nearby_attractions
from tools.weather_tool import get_forecast
from tools.web_search_tool import search_facts
from config.settings import PLANNER_MODEL


def _extract_destination(user_message: str) -> str:
    system_prompt = (
        "Extract ONLY the primary destination city/region from this travel request. "
        "Respond with 1-4 words maximum, just the place name(s), nothing else. No punctuation, no markdown, no sentences.\n\n"
        "Examples:\n"
        "Input: 'plan a 3 day trip to Udaipur with budget and food'\n"
        "Output: Udaipur\n\n"
        "Input: 'maharashtra darshan trip from nagpur, shirdi nashik aurangabad, 6 people, budget planning'\n"
        "Output: Shirdi Nashik Aurangabad\n\n"
        "Input: 'plan a 5 day goa trip with hotels'\n"
        "Output: Goa"
    )
    result = call_llm(
        model=PLANNER_MODEL,
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=20,
    )
    cleaned = result.strip()

    # Validation: extraction failed if it looks like a response, not a place name
    is_invalid = (
        len(cleaned) > 60
        or "\n" in cleaned
        or "#" in cleaned
        or cleaned.count(" ") > 6
    )
    if is_invalid:
        print(f"Destination extraction looked invalid, discarding: {cleaned[:50]}...")
        return ""

    return cleaned


def _extract_origin(user_message: str) -> str:
    system_prompt = (
        "Extract ONLY the origin/starting city mentioned in this travel request — "
        "the city the traveler is starting FROM, not the destination. "
        "Respond with 1-3 words maximum, just the city name. No punctuation, no sentences. "
        "If no origin city is mentioned, respond with exactly: NONE\n\n"
        "Examples:\n"
        "Input: 'plan a trip from nagpur to udaipur'\n"
        "Output: Nagpur\n\n"
        "Input: 'plan a 3 day trip to goa'\n"
        "Output: NONE"
    )
    result = call_llm(
        model=PLANNER_MODEL,
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=15,
    )
    cleaned = result.strip()
    if cleaned.upper() == "NONE" or len(cleaned) > 40 or "\n" in cleaned:
        return ""
    return cleaned


def run_planner_agent(user_message: str, history: str = "") -> str:
    destination = _extract_destination(user_message)

    attractions = nearby_attractions(destination) if destination else []
    forecast = get_forecast(destination) if destination else []

    origin = _extract_origin(user_message)
    if origin and destination:
        first_stop = destination.split()[0]
        route_facts = search_facts(f"travel distance in km and driving time from {origin} to {first_stop} by road")
        if not route_facts:
            route_facts = search_facts(f"travel distance in km and time from {origin} to {destination} by road and train")
    elif destination:
        route_facts = search_facts(f"how to reach {destination}, distance and travel time from major nearby cities")
    else:
        route_facts = ""

    tool_context = ""
    if route_facts:
        tool_context += f"Verified travel facts (live web search):\n{route_facts}\n\n"
    if attractions:
        tool_context += "Nearby attractions (from Google Maps):\n"
        tool_context += "\n".join(f"- {a['name']} ({a.get('rating', 'N/A')}★) - {a['address']}" for a in attractions)
        tool_context += "\n\n"
    if forecast:
        tool_context += "Weather forecast:\n"
        tool_context += "\n".join(f"- {f['date']}: {f['temp_min']}-{f['temp_max']}°C, {f['condition']}" for f in forecast)
        tool_context += "\n\n"

    system_prompt = (
        "You are the Planner Agent of a multilingual tourist assistant. "
        "You create day-wise travel itineraries. "
        "CRITICAL: If 'Verified travel facts' are provided below, you MUST strictly use those distance and travel time numbers "
        "for travel between the origin and destinations. Do NOT guess, underestimate, or invent travel times/distances "
        "(e.g. Nagpur to Shirdi is 470-600+ km and 7-10+ hours, never 120km or 300km). "
        "Weave the tool data (travel facts, attractions, weather) into a practical, realistic plan — "
        "suggest indoor activities on rainy-forecast days, prioritize highly-rated nearby attractions. "
        "If no tool data is available, plan from general knowledge and mention that live data wasn't available. "
        "Respond in the same language/style the user used. Keep it structured (Day 1, Day 2, ...) and practical.\n\n"
        f"{tool_context}"
        + (f"Recent conversation:\n{history}\n\n" if history else "")
    )

    return call_llm(model=PLANNER_MODEL, system_prompt=system_prompt, user_message=user_message, max_tokens=1500)


if __name__ == "__main__":
    print(run_planner_agent("Plan a 3 day trip to Udaipur"))
