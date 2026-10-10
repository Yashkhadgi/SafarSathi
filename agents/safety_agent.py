import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.llm_wrapper import call_llm
from tools.maps_tool import nearby_places_by_type
from tools.translation_tool import translate_text
from config.settings import SAFETY_MODEL


def _extract_location(user_message: str) -> str:
    result = call_llm(
        model=SAFETY_MODEL,
        system_prompt="Extract ONLY the city/place name the user is currently at or near, from this emergency/safety message. Respond with 1-4 words, just the place name, nothing else. If no place is mentioned, respond with exactly: NONE",
        user_message=user_message,
        max_tokens=15,
    )
    cleaned = result.strip()
    if cleaned.upper() == "NONE" or len(cleaned) > 60 or "\n" in cleaned:
        return ""
    return cleaned


def run_safety_agent(user_message: str, history: str = "") -> str:
    location = _extract_location(user_message)
    hospitals = nearby_places_by_type(location, "hospital") if location else []
    police = nearby_places_by_type(location, "police") if location else []

    tool_context = ""
    if hospitals:
        tool_context += "Nearby hospitals:\n" + "\n".join(
            f"- {h['name']} - {h['address']}" for h in hospitals) + "\n\n"
    if police:
        tool_context += "Nearby police stations:\n" + "\n".join(
            f"- {p['name']} - {p['address']}" for p in police) + "\n\n"

    emergency_phrase_hi = translate_text(
        "I need help, this is an emergency. Please call the police or an ambulance.",
        target_lang_code="hi-IN",
    )

    system_prompt = (
        "You are the Emergency/Safety Agent of a multilingual tourist assistant. "
        "The user may be in distress, lost, or facing an emergency. Be calm, clear, "
        "and prioritize actionable safety information: nearest hospital/police (if "
        "provided below), India's emergency numbers (112 for all emergencies, 100 "
        "police, 108 ambulance), and the translated emergency phrase below they can "
        "show or say to a local person. Keep the response short and practical, no "
        "fluff. Respond in the same language/style the user used.\n\n"
        f"{tool_context}"
        f"Emergency phrase in Hindi (for the user to show/say if needed): {emergency_phrase_hi}\n\n"
        + (f"Recent conversation:\n{history}\n\n" if history else "")
    )
    return call_llm(model=SAFETY_MODEL, system_prompt=system_prompt, user_message=user_message, max_tokens=600)


if __name__ == "__main__":
    print(run_safety_agent("I'm in Udaipur and I think I lost my wallet, I need help"))
