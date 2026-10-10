"""Source-aware adapters for the original P0 tool set."""

from datetime import datetime, timezone


def search_knowledge_base(query, place=None, category=None):
    try:
        from agents.rag_agent import retrieve

        return retrieve(query, place=place, category=category)
    except Exception as exc:
        return {"error": str(exc)}


def get_weather(place, days=3):
    try:
        from config.settings import OPENWEATHER_API_KEY
        from tools.weather_tool import get_forecast

        if not OPENWEATHER_API_KEY:
            return {"error": "Live weather is unavailable; OPENWEATHER_API_KEY is not set"}
        forecast = get_forecast(place, days)
        if not forecast:
            return {"error": "Live weather is unavailable"}
        return {"place": place, "forecast": forecast,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "source_name": "OpenWeather"}
    except Exception as exc:
        return {"error": str(exc)}


def get_nearby_places(place, place_type="tourist_attraction", limit=5):
    try:
        from config.settings import GOOGLE_MAPS_API_KEY
        from tools.maps_tool import nearby_places_by_type

        if not GOOGLE_MAPS_API_KEY:
            return {"error": "Live nearby places are unavailable; GOOGLE_MAPS_API_KEY is not set"}
        places = nearby_places_by_type(place, place_type, limit=min(int(limit), 10))
        if not places:
            return {"error": "No live nearby places available"}
        return {"place": place, "places": places, "source_name": "Google Maps",
                "retrieved_at": datetime.now(timezone.utc).isoformat()}
    except Exception as exc:
        return {"error": str(exc)}


def web_search(query):
    try:
        from config.settings import TAVILY_API_KEY
        from memory.cache import cached_call

        if not TAVILY_API_KEY:
            return {"error": "Live web search is unavailable; TAVILY_API_KEY is not set"}
        from tavily import TavilyClient

        response = cached_call(
            "tavily_search", [query], 6 * 3600,
            lambda: TavilyClient(api_key=TAVILY_API_KEY).search(
                query=query, search_depth="basic", max_results=5
            ),
        )
        results = [
            {"title": item.get("title", ""), "url": item.get("url", ""),
             "snippet": item.get("content", "")}
            for item in response.get("results", []) if item.get("url")
        ]
        return {"results": results, "retrieved_at": datetime.now(timezone.utc).isoformat()}
    except Exception as exc:
        return {"error": str(exc)}


def translate_text(text, target_lang_code, source_lang_code="en-IN"):
    try:
        from config.settings import SARVAM_API_KEY
        from tools.translation_tool import translate_text as translate

        if not SARVAM_API_KEY:
            return {"error": "Live translation is unavailable; SARVAM_API_KEY is not set"}
        result = translate(text, target_lang_code=target_lang_code,
                           source_lang_code=source_lang_code)
        return {"text": result} if result and result != text else {"error": "Translation unavailable"}
    except Exception as exc:
        return {"error": str(exc)}
