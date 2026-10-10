# Monkey-patch gradio_client for compatibility with modern Pydantic boolean schemas
try:
    import gradio_client.utils as _gc_utils
    _orig_get_type = _gc_utils.get_type
    _orig_json_schema = _gc_utils._json_schema_to_python_type

    def _safe_get_type(schema):
        if not isinstance(schema, dict):
            return {}
        return _orig_get_type(schema)

    def _safe_json_schema(schema, defs):
        if not isinstance(schema, dict) or schema == {}:
            return "Any"
        return _orig_json_schema(schema, defs)

    _gc_utils.get_type = _safe_get_type
    _gc_utils._json_schema_to_python_type = _safe_json_schema
except Exception:
    pass

import gradio as gr
import sys
import os
import tempfile
import json
import html
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import ANTHROPIC_API_KEY, USE_TOOL_AGENT
from memory.session_memory import create_session, ensure_session, get_history, list_user_sessions, save_turn
from memory.language_preferences import get_session_preferences, save_session_preferences
from tools.currency_tool import convert_currency
from tools.voice_tool import speech_to_text, text_to_speech

PROJECT_ROOT = Path(__file__).resolve().parents[1]
with (PROJECT_ROOT / "data" / "emergency" / "india.json").open(encoding="utf-8") as _emergency_file:
    EMERGENCY_DATA = json.load(_emergency_file)
with (PROJECT_ROOT / "data" / "emergency" / "phrases.json").open(encoding="utf-8") as _phrases_file:
    EMERGENCY_PHRASES = json.load(_phrases_file)["phrases"]


def _run_agent(session_id, message, language_override="auto", show_english=False):
    from memory.cache import reset_scope, set_scope
    from memory.usage import check_and_record_message, record_reply

    owner_id = session_id.split(":", 1)[0]
    admitted = check_and_record_message(owner_id, message)
    if "error" in admitted:
        return "Rate limit", admitted["error"]
    scope = set_scope(owner_id)
    try:
        if message.strip().casefold() in {"mere saved trips", "mere saved trips dikhao", "my saved trips", "show my saved trips"}:
            from memory.trips import list_trips

            trips = list_trips(owner_id)
            response = ("\n".join(f"- {item['title']} (version {item['version']})"
                                  for item in trips) if trips else "No saved trips yet.")
            save_turn(session_id, "user", message)
            save_turn(session_id, "assistant", response)
            record_reply(owner_id, response)
            return "Saved Trips", response
        if not ANTHROPIC_API_KEY:
            return "Assistant unavailable", "Chat requires an Anthropic API key. SOS information remains available."
        from agents.orchestrator_graph import run_agent

        result = run_agent(
            session_id,
            message,
            language_override=language_override,
            show_english=show_english,
        )
        record_reply(owner_id, result[1])
        return result
    except Exception as exc:
        return "Assistant unavailable", f"The assistant could not start: {exc}"
    finally:
        reset_scope(scope)


def _sos_static_panel():
    lines = ["## Emergency numbers (India)", ""]
    for item in EMERGENCY_DATA["numbers"]:
        lines.append(f"**{item['label']}: {item['number']}**  \n{item['note']}")
    lines.extend(["", "### Emergency phrases"])
    lines.extend(f"**{item['language']}:** {item['text']}" for item in EMERGENCY_PHRASES)
    lines.extend(["", f"Last verified: {EMERGENCY_DATA['last_verified']}", "", "For immediate danger, call 112. Nearby place lookup is optional and may need internet and a Maps key."])
    return "\n\n".join(lines)


def open_sos_panel():
    return gr.update(visible=True), _sos_static_panel(), "", "", ""


def lookup_emergency_services(city, latitude, longitude, location_allowed=True):
    if not location_allowed:
        return "Enable location consent in Privacy, or enter a city manually.", "", ""
    resolved_latitude, resolved_longitude = latitude or "", longitude or ""
    try:
        from tools.maps_tool import get_place_coordinates, nearest_emergency_services

        if resolved_latitude and resolved_longitude:
            places = nearest_emergency_services(latitude=resolved_latitude, longitude=resolved_longitude)
        elif city and city.strip():
            coordinates = get_place_coordinates(city.strip())
            if coordinates:
                resolved_latitude = str(coordinates["latitude"])
                resolved_longitude = str(coordinates["longitude"])
                places = nearest_emergency_services(latitude=resolved_latitude, longitude=resolved_longitude)
            else:
                places = {"hospitals": [], "police": []}
        else:
            return "Allow location access or enter a city/area below.", "", ""
        if not places.get("hospitals") and not places.get("police"):
            return "Nearby service lookup is unavailable. The emergency numbers above remain available.", resolved_latitude, resolved_longitude
        lines = ["### Nearby emergency services"]
        for label, title in (("hospitals", "Hospitals"), ("police", "Police")):
            found = places.get(label, [])
            if found:
                lines.append(f"**{title}**")
                lines.extend(
                    f"- {item['name']} — {item.get('address') or 'Address unavailable'} ({item['distance_m']} m)"
                    for item in found
                )
        return "\n".join(lines), resolved_latitude, resolved_longitude
    except Exception:
        return "Nearby service lookup is unavailable. The emergency numbers above remain available.", resolved_latitude, resolved_longitude


def lookup_emergency_by_city(city):
    return lookup_emergency_services(city, "", "")


def sos_phrase_ui(language):
    from tools.phrasebook import emergency_phrase

    item = emergency_phrase(language)
    if "error" in item:
        return item["error"], None
    return item["text"], item["audio_path"]


def sos_big_phrase_ui(language):
    from tools.phrasebook import emergency_phrase

    item = emergency_phrase(language)
    if "error" in item:
        return html.escape(item["error"])
    return ("<div style='display:grid;place-items:center;min-height:50vh;padding:5vw;"
            "background:#fff;color:#111;font-size:clamp(32px,6vw,70px);text-align:center'>"
            + html.escape(item["text"]) + "</div>")


def phrasebook_ui(situation, language):
    from tools.phrasebook import phrase_for

    item = phrase_for(situation, language)
    if "error" in item:
        return item["error"], None
    return (f"## {html.escape(item['text'])}\n\n"
            f"Pronunciation: {html.escape(item['pronunciation'])}\n\n"
            "Translation draft; native-speaker review pending."), item["audio_path"]


def live_translate_ui(audio_path, typed_text, speaker, language_a, language_b, history,
                      user_id, request: gr.Request):
    from ui.live_translation import translate_turn

    result = translate_turn(audio_path, typed_text, speaker, language_a, language_b, history,
                            user_id=_request_user_id(request, user_id))
    if "error" in result:
        return "", "", None, result["history"], result["error"], ""
    turn = result["turn"]
    history_lines = []
    for row in result["history"]:
        history_lines.append(f"**{row['speaker']}** ({row['detected_language']} → {row['target_language']})  \n"
                             f"{html.escape(row['original'])}  \n"
                             f"{html.escape(row['translated'])}")
    status = f"{turn['status']} · {turn['latency_seconds']} s"
    return (turn["original"], turn["translated"], turn["audio_path"],
            result["history"], status, "\n\n".join(history_lines))


def live_translate_a_ui(audio_path, typed_text, language_a, language_b, history,
                        user_id, request: gr.Request):
    return live_translate_ui(audio_path, typed_text, "A", language_a, language_b,
                             history, user_id, request)


def live_translate_b_ui(audio_path, typed_text, language_a, language_b, history,
                        user_id, request: gr.Request):
    return live_translate_ui(audio_path, typed_text, "B", language_a, language_b,
                             history, user_id, request)


def _detected_label(message):
    from agents.language_agent import LANGUAGES, detect_language

    code = detect_language(message)
    return f"Detected: {LANGUAGES.get(code, code)}"


def find_nearby_ui(city, latitude, longitude, kind, open_now, veg, min_rating,
                   location_allowed):
    from tools.realtime_tool import near_me

    result = near_me(latitude or None, longitude or None, city=city.strip(), kind=kind,
                     open_now=open_now, veg=veg, min_rating=min_rating,
                     consent=location_allowed)
    if "error" in result:
        return result["error"]
    if not result["results"]:
        return "No matching places returned. Try another category or fewer filters."
    rows = ["| Place | Distance | Open now | Rating |", "|---|---:|---|---:|"]
    for item in result["results"]:
        name = html.escape(item["name"]).replace("|", "\\|")
        opened = item["open_now"]
        open_label = "Yes" if opened is True else "No" if opened is False else "verify"
        rating = item["rating"] if item["rating"] is not None else "verify"
        rows.append(f"| {name} | approx {item['distance_km']} km | {open_label} | {rating} |")
    rows.append(f"\nSource: [Google Places]({result['source_url']}) | Last verified: {result['last_verified']}")
    return "\n".join(rows)


def _trusted_contact_choices(user_id):
    from memory.trusted_contacts import list_contacts

    contacts = list_contacts(user_id)
    choices = [(f"{item['name']} · {item['phone']}", str(item["contact_id"])) for item in contacts]
    rows = ["- **{}** · {}".format(html.escape(item["name"]).replace("|", "\\|"), item["phone"]) for item in contacts]
    return choices, "\n".join(rows) if rows else "No trusted contacts saved."


def _contact_ui_refresh(user_id, status=""):
    choices, listing = _trusted_contact_choices(user_id)
    return status, gr.update(choices=choices, value=None), gr.update(choices=choices, value=None), listing


def save_trusted_contact(name, phone, user_id, consent, contacts_allowed, request: gr.Request):
    from memory.trusted_contacts import add_contact

    owner_id = _request_user_id(request, user_id)
    result = add_contact(owner_id, name, phone, consent and contacts_allowed)
    status = "Contact saved." if "error" not in result else result["error"]
    return _contact_ui_refresh(owner_id, status)


def remove_trusted_contact(contact_id, user_id, request: gr.Request):
    from memory.trusted_contacts import delete_contact

    owner_id = _request_user_id(request, user_id)
    result = delete_contact(owner_id, contact_id)
    status = "Contact deleted." if result.get("deleted") else result.get("error", "Could not delete contact.")
    return _contact_ui_refresh(owner_id, status)


def prepare_location_message(contact_id, template, latitude, longitude, user_id, request: gr.Request):
    from memory.trusted_contacts import create_share_links

    owner_id = _request_user_id(request, user_id)
    result = create_share_links(owner_id, contact_id, template, latitude, longitude)
    if "error" in result:
        return result["error"]
    return (
        f"Prepared for **{html.escape(result['name'])}**. Choose a link to open your messaging app; "
        "nothing is sent by this app.\n\n"
        f"{result['message']}\n\n"
        f"[Open WhatsApp]({result['whatsapp_url']}) · [Open SMS]({result['sms_url']})"
    )


# ── Chat handler ──────────────────────────────────────────────────────────────
def _request_user_id(request: gr.Request, fallback_user_id: str = "") -> str:
    from memory.auth import browser_user

    session_hash = getattr(request, "session_hash", None)
    if session_hash:
        account_id = browser_user(session_hash)
        if account_id:
            return account_id
        return f"gradio-{session_hash}"
    return fallback_user_id or "gradio-anonymous"


def _session_choices(user_id: str):
    return [
        (f"{session['title']} · {session['created_at'][:16]}", session["session_id"])
        for session in list_user_sessions(user_id)
    ]


def _history_for_chatbot(session_id: str):
    turns = get_history(session_id, max_turns=100)
    chatbot_history = []
    pending_user = None
    for role, content in turns:
        if role == "user":
            if pending_user is not None:
                chatbot_history.append((pending_user, None))
            pending_user = content
        elif role == "assistant":
            if pending_user is None:
                chatbot_history.append((None, content))
            else:
                chatbot_history.append((pending_user, content))
                pending_user = None
    if pending_user is not None:
        chatbot_history.append((pending_user, None))
    return chatbot_history


def initialize_session(user_id, session_id, request: gr.Request):
    from memory.privacy import get_consents
    from memory.profiles import FIELDS, get_profile
    from memory.trips import list_trips
    from memory.favorites import list_favorites

    user_id = _request_user_id(request, user_id)
    session_id = ensure_session(user_id, session_id)
    choices, contact_listing = _trusted_contact_choices(user_id)
    language_preferences = get_session_preferences(session_id)
    consents = get_consents(user_id)
    profile = get_profile(user_id)
    trips = list_trips(user_id)
    return (
        user_id,
        session_id,
        gr.update(choices=_session_choices(user_id), value=session_id),
        _history_for_chatbot(session_id),
        gr.update(choices=choices, value=None),
        gr.update(choices=choices, value=None),
        contact_listing,
        gr.update(value=language_preferences["language_code"]),
        gr.update(value=language_preferences["show_english"]),
        gr.update(value=consents["location"]),
        gr.update(value=consents["contacts"]),
        _usage_label(user_id),
        *(gr.update(value=profile[field]) for field in FIELDS),
        gr.update(choices=[(f"{item['title']} · v{item['version']}", item["trip_id"]) for item in trips], value=None),
        _favorites_markdown(list_favorites(user_id)),
        gr.update(choices=[(item["title"], item["trip_id"]) for item in trips], value=None),
        [],
        "",
    )


def _usage_label(user_id):
    from memory.usage import usage_today

    usage = usage_today(user_id)
    return (f"Calls today: {usage['calls_today']} | approx tokens: "
            f"{usage['approx_tokens_today']}/{usage['daily_token_cap']}")


def _favorites_markdown(favorites):
    if not favorites:
        return "No favorite places saved."
    return "\n".join(f"- {html.escape(item['place'])}" for item in favorites)


def refresh_map_trips_ui(user_id, request: gr.Request):
    from memory.trips import list_trips

    trips = list_trips(_request_user_id(request, user_id))
    return gr.update(choices=[(item["title"], item["trip_id"]) for item in trips], value=None)


def show_trip_map_ui(trip_id, selected_day, user_id, request: gr.Request):
    from memory.trips import get_trip
    from tools.map_view import trip_map

    if not trip_id:
        return "", "Choose a saved trip.", gr.update(choices=[("All days", "all")], value="all")
    trip = get_trip(trip_id, user_id=_request_user_id(request, user_id))
    if "error" in trip:
        return "", trip["error"], gr.update(choices=[("All days", "all")], value="all")
    valid_days = [str(day.get("day")) for day in trip.get("days", [])]
    selected_day = str(selected_day) if str(selected_day) in valid_days else "all"
    result = trip_map(trip, selected_day)
    if "error" in result:
        return "", result["error"], gr.update(value=selected_day)
    status = f"{result['mapped']} mapped stops. Source: [OpenStreetMap]({result['source_url']})."
    if result["missing"]:
        status += " Could not locate: " + ", ".join(html.escape(name) for name in result["missing"])
    choices = [("All days", "all"), *[(f"Day {day}", day) for day in valid_days]]
    return result["html"], status, gr.update(choices=choices, value=selected_day)


def record_chat_feedback(user_id, session_id, reason, comment, request: gr.Request,
                         evt: gr.LikeData):
    from memory.feedback import save_feedback

    owner_id = _request_user_id(request, user_id)
    index = evt.index[0] if isinstance(evt.index, (tuple, list)) else evt.index
    result = save_feedback(owner_id, session_id, index, 1 if evt.liked else -1,
                           reason or "", comment or "")
    return result.get("error", "Feedback saved. Thank you.")


def save_profile_ui(interests, diet, allergies, budget_range, mobility, languages,
                    home_city, travel_style, user_id, request: gr.Request):
    from memory.profiles import FIELDS, save_profile

    values = (interests, diet, allergies, budget_range, mobility, languages,
              home_city, travel_style)
    result = save_profile(_request_user_id(request, user_id), dict(zip(FIELDS, values)))
    return result.get("error", "Profile saved.")


def delete_profile_ui(user_id, request: gr.Request):
    from memory.profiles import FIELDS, delete_profile

    result = delete_profile(_request_user_id(request, user_id))
    return (result.get("error", "Profile deleted."),
            *(gr.update(value="") for _ in FIELDS))


def _trip_choices(user_id):
    from memory.trips import list_trips

    return [(f"{item['title']} · v{item['version']}", item["trip_id"])
            for item in list_trips(user_id)]


def refresh_trips_ui(user_id, request: gr.Request):
    from memory.favorites import list_favorites

    owner_id = _request_user_id(request, user_id)
    return gr.update(choices=_trip_choices(owner_id), value=None), _favorites_markdown(list_favorites(owner_id))


def show_saved_trip_ui(trip_id, user_id, request: gr.Request):
    from memory.trips import get_trip
    from tools.itinerary_tool import itinerary_markdown

    if not trip_id:
        return ""
    result = get_trip(trip_id, user_id=_request_user_id(request, user_id))
    return result["error"] if "error" in result else itinerary_markdown(result)


def change_saved_trip_ui(trip_id, title, action, user_id, request: gr.Request):
    from memory.trips import delete_trip, duplicate_trip, rename_trip

    owner_id = _request_user_id(request, user_id)
    if action == "rename":
        result = rename_trip(trip_id, owner_id, title)
    elif action == "duplicate":
        result = duplicate_trip(trip_id, owner_id)
    else:
        result = delete_trip(trip_id, owner_id)
    status = result.get("error", f"Trip {action}d.")
    return status, gr.update(choices=_trip_choices(owner_id), value=None), ""


def rename_saved_trip_ui(trip_id, title, user_id, request: gr.Request):
    return change_saved_trip_ui(trip_id, title, "rename", user_id, request)


def duplicate_saved_trip_ui(trip_id, user_id, request: gr.Request):
    return change_saved_trip_ui(trip_id, "", "duplicate", user_id, request)


def delete_saved_trip_ui(trip_id, user_id, request: gr.Request):
    return change_saved_trip_ui(trip_id, "", "delete", user_id, request)


def add_favorite_ui(place, source_url, user_id, request: gr.Request):
    from memory.favorites import add_favorite, list_favorites

    owner_id = _request_user_id(request, user_id)
    result = add_favorite(owner_id, place, source_url)
    return result.get("error", "Favorite saved."), _favorites_markdown(list_favorites(owner_id))


def remove_favorite_ui(place, user_id, request: gr.Request):
    from memory.favorites import list_favorites, remove_favorite

    owner_id = _request_user_id(request, user_id)
    result = remove_favorite(owner_id, place)
    return result.get("error", "Favorite removed."), _favorites_markdown(list_favorites(owner_id))


def _account_action(email, password, mode, user_id, session_id, request: gr.Request):
    from memory.auth import login_account, register_account

    session_hash = getattr(request, "session_hash", "")
    result = (register_account if mode == "register" else login_account)(
        email, password, session_hash
    )
    if "error" in result:
        return (result["error"],) + initialize_session(user_id, session_id, request)
    return ("Signed in.",) + initialize_session(result["user_id"], "", request)


def register_ui(email, password, user_id, session_id, request: gr.Request):
    return _account_action(email, password, "register", user_id, session_id, request)


def login_ui(email, password, user_id, session_id, request: gr.Request):
    return _account_action(email, password, "login", user_id, session_id, request)


def logout_ui(user_id, session_id, request: gr.Request):
    from memory.auth import logout_account

    result = logout_account(getattr(request, "session_hash", ""))
    status = result.get("error", "Signed out.")
    return (status,) + initialize_session("", "", request)


def delete_my_data_ui(user_id, session_id, confirmed, request: gr.Request):
    from memory.privacy import delete_all_user_data

    if not confirmed:
        return ("Check the confirmation box before deleting data.",) + initialize_session(user_id, session_id, request)
    owner_id = _request_user_id(request, user_id)
    result = delete_all_user_data(owner_id)
    status = result.get("error", "Your local data was deleted.")
    return (status,) + initialize_session("", "", request)


def save_privacy_ui(location, contacts, user_id, request: gr.Request):
    from memory.privacy import set_consents

    result = set_consents(_request_user_id(request, user_id), location, contacts)
    return result.get("error", "Privacy choices saved.")


def start_new_chat(user_id, language_code, show_english, request: gr.Request):
    user_id = _request_user_id(request, user_id)
    session_id = create_session(user_id)
    save_session_preferences(session_id, language_code=language_code, show_english=show_english)
    return (
        session_id,
        gr.update(choices=_session_choices(user_id), value=session_id),
        [],
    )


def load_selected_chat(selected_session_id, user_id, request: gr.Request):
    user_id = _request_user_id(request, user_id)
    session_id = ensure_session(user_id, selected_session_id)
    language_preferences = get_session_preferences(session_id)
    return (
        session_id,
        gr.update(choices=_session_choices(user_id), value=session_id),
        _history_for_chatbot(session_id),
        gr.update(value=language_preferences["language_code"]),
        gr.update(value=language_preferences["show_english"]),
    )


def chat_with_agent(message, history, user_id, session_id, language_code, show_english, request: gr.Request):
    if not message or not message.strip():
        return "", history or [], session_id, gr.update(), _usage_label(_request_user_id(request, user_id))

    user_id = _request_user_id(request, user_id)
    session_id = ensure_session(user_id, session_id)
    history = history or []
    history.append((message, None))

    agent_name, response = _run_agent(session_id, message, language_code, show_english)
    history[-1] = (message, f"**[{_detected_label(message)} · Routed to: {agent_name}]**\n\n{response}")
    return (
        "",
        history,
        session_id,
        gr.update(choices=_session_choices(user_id), value=session_id),
        _usage_label(user_id),
    )


def chat_with_agent_stream(message, history, user_id, session_id, language_code,
                           show_english, request: gr.Request):
    from agents.core_agent import stream_core_agent
    from agents.guardrails import post_process_answer
    from agents.language_agent import detect_language, input_normalizer, output_localizer
    from agents.scam_alerts import auto_attach_scam_alerts
    from memory.cache import reset_scope, set_scope
    from memory.language_preferences import get_session_preferences, save_session_preferences
    from memory.profiles import save_from_chat
    from memory.usage import check_and_record_message, record_reply

    owner_id = _request_user_id(request, user_id)
    if not message or not message.strip():
        yield "", history or [], session_id, gr.update(), _usage_label(owner_id)
        return
    session_id = ensure_session(owner_id, session_id)
    history = list(history or [])
    history.append((message, "Preparing reply..."))
    yield "", history, session_id, gr.update(choices=_session_choices(owner_id), value=session_id), _usage_label(owner_id)

    admitted = check_and_record_message(owner_id, message)
    if "error" in admitted:
        history[-1] = (message, admitted["error"])
        yield "", history, session_id, gr.update(), _usage_label(owner_id)
        return
    scope = set_scope(owner_id)
    try:
        if not ANTHROPIC_API_KEY:
            history[-1] = (message, "Chat requires an Anthropic API key. SOS remains available.")
            yield "", history, session_id, gr.update(), _usage_label(owner_id)
            return
        preferences = get_session_preferences(session_id)
        preference = language_code or preferences["language_code"]
        detected = detect_language(message, preference)
        normalized = input_normalizer(message, detected)
        save_from_chat(owner_id, message)
        save_turn(session_id, "user", message)
        final = None
        for event in stream_core_agent(session_id, normalized):
            if "partial" in event and (detected == "en-IN" or show_english):
                history[-1] = (message, event["partial"])
                yield "", history, session_id, gr.update(), _usage_label(owner_id)
            elif "status" in event:
                history[-1] = (message, event["status"])
                yield "", history, session_id, gr.update(), _usage_label(owner_id)
            elif event.get("done"):
                final = event
        if final is None:
            return
        answer = post_process_answer(
            final["answer"], user_message=normalized,
            tool_results=final.get("tool_results", []),
        )
        answer = auto_attach_scam_alerts(answer, user_message=normalized)
        answer = output_localizer(answer, detected, show_english=show_english)
        used = list(dict.fromkeys(final.get("tools_used", [])))
        if used:
            answer += "\n\nUsed: " + ", ".join(used)
        save_session_preferences(
            session_id, language_code=preference, detected_language=detected,
            show_english=show_english,
        )
        save_turn(session_id, "assistant", answer)
        record_reply(owner_id, answer)
        history[-1] = (message, f"**[Detected: {detected}]**\n\n{answer}")
        yield "", history, session_id, gr.update(choices=_session_choices(owner_id), value=session_id), _usage_label(owner_id)
    except Exception as exc:
        history[-1] = (message, f"Assistant unavailable: {exc}")
        yield "", history, session_id, gr.update(), _usage_label(owner_id)
    finally:
        reset_scope(scope)


# ── Currency handler ──────────────────────────────────────────────────────────
def do_convert(amount, from_cur, to_cur):
    result = convert_currency(float(amount), from_cur, to_cur)
    if "error" in result:
        return f"Error: {result['error']}"
    return f"{amount} {from_cur} = {result['converted_amount']} {to_cur}  (rate: {result['rate']})"


# ── Voice handler ─────────────────────────────────────────────────────────────
def handle_voice(audio_path, voice_lang, user_id, session_id, language_code, show_english, request: gr.Request):
    """
    audio_path: file path Gradio gives us from gr.Audio(type='filepath')
    voice_lang: language code selected by user (hi-IN, en-IN, etc.)
    Returns: (transcript_text, agent_reply_text, audio_reply_path, session_id)
    """
    user_id = _request_user_id(request, user_id)
    session_id = ensure_session(user_id, session_id)

    if audio_path is None:
        return "❌ No audio recorded.", "", None, session_id, gr.update(), _usage_label(user_id)

    # Step 1: Read audio file
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        file_ext = os.path.splitext(audio_path)[-1].lstrip(".") or "wav"
    except Exception as e:
        return f"❌ Could not read audio: {e}", "", None, session_id, gr.update(), _usage_label(user_id)

    # Step 2: STT — audio → text
    transcript = speech_to_text(audio_bytes, file_format=file_ext, lang_code=voice_lang)
    if not transcript:
        return "❌ Could not understand audio. Please speak clearly and try again.", "", None, session_id, gr.update(), _usage_label(user_id)

    # Step 3: Route through agent
    agent_name, reply_text = _run_agent(session_id, transcript, language_code, show_english)
    display_reply = f"**[{_detected_label(transcript)} · Routed to: {agent_name}]**\n\n{reply_text}"

    # Step 4: TTS — agent reply → audio
    from agents.language_agent import detect_language
    reply_language = detect_language(reply_text)
    tts_lang = reply_language if reply_language in {"hi-IN", "bn-IN", "ta-IN", "te-IN", "mr-IN", "gu-IN", "kn-IN"} else "en-IN"
    if not show_english and reply_language in ("en-IN", "hinglish"):
        tts_lang = "hi-IN" if language_code == "hinglish" else (language_code if language_code != "auto" else voice_lang)
    if tts_lang == "hinglish":
        tts_lang = "hi-IN"
    speaker = "advait"

    audio_bytes_out = text_to_speech(reply_text, lang_code=tts_lang, speaker=speaker)

    audio_output_path = None
    if audio_bytes_out:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(audio_bytes_out)
        tmp.close()
        audio_output_path = tmp.name

    return (
        transcript,
        display_reply,
        audio_output_path,
        session_id,
        gr.update(choices=_session_choices(user_id), value=session_id),
        _usage_label(user_id),
    )


def save_language_ui_preference(language_code, show_english, user_id, session_id, request: gr.Request):
    owner_id = _request_user_id(request, user_id)
    session_id = ensure_session(owner_id, session_id)
    saved = save_session_preferences(
        session_id,
        language_code=language_code,
        show_english=show_english,
    )
    return "Language preference saved for this chat." if saved else "Could not save language preference; current selection still applies."


# ── Styling ───────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
:root, .dark {
    --body-background-fill: #1a1a17;
    --background-fill-primary: #1a1a17;
    --background-fill-secondary: #24241f;
    --block-background-fill: #24241f;
    --border-color-primary: #4b4b3a;
    --body-text-color: #e8e6dc;
    --block-title-text-color: #e8e6dc;
    --button-primary-background-fill: #556b2f;
    --button-primary-background-fill-hover: #6b8536;
    --button-primary-text-color: #f5f5ef;
}
body, .gradio-container {
    background-color: #1a1a17 !important;
}
.message.user {
    background-color: #556b2f !important;
    color: #f5f5ef !important;
}
.message.bot {
    background-color: #24241f !important;
    color: #e8e6dc !important;
    border: 1px solid #4b4b3a !important;
}
.voice-hint {
    font-size: 0.85rem;
    color: #a0a08a;
    margin-top: 4px;
}
.sos-button {
    background: #c62828 !important;
    color: white !important;
    border: 2px solid #ffb4ab !important;
    font-weight: 800 !important;
    min-height: 48px !important;
}
.sos-panel {
    border: 2px solid #c62828 !important;
    border-radius: 6px !important;
    padding: 12px !important;
}
"""

theme = gr.themes.Base(
    primary_hue=gr.themes.colors.green,
    neutral_hue=gr.themes.colors.stone,
).set(
    body_background_fill="#1a1a17",
    block_background_fill="#24241f",
    border_color_primary="#4b4b3a",
)

CURRENCY_CHOICES = ["INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "AED", "SGD"]

LANG_CHOICES = [
    ("Hindi (हिन्दी)", "hi-IN"),
    ("English", "en-IN"),
    ("Bengali (বাংলা)", "bn-IN"),
    ("Tamil (தமிழ்)", "ta-IN"),
    ("Telugu (తెలుగు)", "te-IN"),
    ("Marathi (मराठी)", "mr-IN"),
    ("Gujarati (ગુજરાતી)", "gu-IN"),
    ("Kannada (ಕನ್ನಡ)", "kn-IN"),
]


# ── Build UI ──────────────────────────────────────────────────────────────────
with gr.Blocks(theme=theme, css=CUSTOM_CSS, title="🧳 Multilingual Tourist Assistant") as demo:
    user_state = gr.State("")
    session_state = gr.State("")
    live_translation_state = gr.State([])

    gr.Markdown(
        "# 🧳 Multilingual Tourist Assistant\n"
        "Plan trips · Get local info · Emergency help · Cultural tips · Voice support"
    )

    sos_button = gr.Button("SOS", elem_classes=["sos-button"])
    with gr.Group(visible=False, elem_classes=["sos-panel"]) as sos_panel:
        sos_static = gr.Markdown()
        with gr.Row():
            sos_language = gr.Dropdown(choices=LANG_CHOICES, value="hi-IN", label="Emergency phrase")
            sos_show = gr.Button("Show to local")
        sos_selected_phrase = gr.Markdown()
        sos_phrase_audio = gr.Audio(label="Offline emergency audio", type="filepath", interactive=False)
        sos_large = gr.HTML(elem_id="sos-large-display")
        sos_language.change(fn=sos_phrase_ui, inputs=[sos_language],
                            outputs=[sos_selected_phrase, sos_phrase_audio], queue=False)
        sos_show.click(fn=sos_big_phrase_ui, inputs=[sos_language], outputs=[sos_large],
                       js="""(code) => { const area = document.getElementById('sos-large-display');
                           if (area && area.requestFullscreen) area.requestFullscreen(); return code; }""",
                       queue=False)
        gr.Markdown("### Find nearby help")
        with gr.Row():
            get_location_btn = gr.Button("Use my location", variant="primary")
            sos_city = gr.Textbox(label="Or enter city / area", placeholder="e.g. Jaipur")
            sos_city_btn = gr.Button("Search city")
        sos_latitude = gr.Textbox(visible=False, value="")
        sos_longitude = gr.Textbox(visible=False, value="")
        nearby_services = gr.Markdown()
        gr.Markdown("### Share location with a trusted contact")
        with gr.Row():
            share_contact = gr.Dropdown(choices=[], label="Trusted contact", scale=2)
            share_template = gr.Dropdown(
                choices=[("I'm safe", "safe"), ("I need help", "help")],
                value="help",
                label="Message",
                scale=1,
            )
            share_location_btn = gr.Button("Share location", variant="secondary")
        share_links = gr.Markdown()

    with gr.Row():
        language_dropdown = gr.Dropdown(
            choices=[("Auto detect", "auto"), *LANG_CHOICES, ("Hinglish", "hinglish")],
            value="auto",
            label="Reply language",
            scale=2,
        )
        show_english = gr.Checkbox(label="Show in English", value=False, scale=1)
        language_status = gr.Markdown()

    language_dropdown.change(
        fn=save_language_ui_preference,
        inputs=[language_dropdown, show_english, user_state, session_state],
        outputs=[language_status],
        queue=False,
    )
    show_english.change(
        fn=save_language_ui_preference,
        inputs=[language_dropdown, show_english, user_state, session_state],
        outputs=[language_status],
        queue=False,
    )

    sos_button.click(
        fn=open_sos_panel,
        inputs=[],
        outputs=[sos_panel, sos_static, nearby_services, sos_latitude, sos_longitude],
        queue=False,
    )
    sos_city_btn.click(
        fn=lookup_emergency_by_city,
        inputs=[sos_city],
        outputs=[nearby_services, sos_latitude, sos_longitude],
        queue=False,
    )
    share_location_btn.click(
        fn=prepare_location_message,
        inputs=[share_contact, share_template, sos_latitude, sos_longitude, user_state],
        outputs=[share_links],
        queue=False,
    )

    # ── Tab 1: Chat ────────────────────────────────────────────────────────
    with gr.Tab("💬 Chat"):
        gr.Markdown("Type your query — routes to Planner, Info, Safety, or Etiquette agent automatically.")
        with gr.Row():
            new_chat_btn = gr.Button("New chat", variant="secondary")
            chat_picker = gr.Dropdown(
                choices=[],
                label="Previous chats",
                interactive=True,
                scale=3,
            )
        chatbot = gr.Chatbot(likeable=True, height=500)
        usage_status = gr.Markdown()
        with gr.Row():
            feedback_reason = gr.Dropdown(
                choices=[("Reason (optional)", ""), ("Wrong information", "wrong_info"),
                         ("Too long", "too_long"), ("Language", "language"),
                         ("Other", "other")], value="", label="Feedback reason",
            )
            feedback_comment = gr.Textbox(label="Feedback comment (optional)", max_lines=2)
        feedback_status = gr.Markdown()
        chatbot.like(
            fn=record_chat_feedback,
            inputs=[user_state, session_state, feedback_reason, feedback_comment],
            outputs=[feedback_status],
        )
        with gr.Row():
            chat_input = gr.Textbox(
                label="Message",
                placeholder="Ask about a destination, itinerary, safety, or local etiquette...",
                scale=5,
            )
            send_btn = gr.Button("Send", variant="primary")
            stop_btn = gr.Button("Stop", variant="secondary")

        with gr.Accordion("💱 Currency Converter", open=False):
            with gr.Row():
                amount_input = gr.Number(value=100, label="Amount")
                from_cur = gr.Dropdown(choices=CURRENCY_CHOICES, value="INR", label="From")
                to_cur = gr.Dropdown(choices=CURRENCY_CHOICES, value="USD", label="To")
            convert_btn = gr.Button("Convert", variant="primary")
            result_box = gr.Textbox(label="Result", interactive=False)
            convert_btn.click(fn=do_convert, inputs=[amount_input, from_cur, to_cur], outputs=result_box)

        chat_submit_inputs = [chat_input, chatbot, user_state, session_state, language_dropdown, show_english]
        chat_submit_outputs = [chat_input, chatbot, session_state, chat_picker, usage_status]
        chat_handler = chat_with_agent_stream if USE_TOOL_AGENT else chat_with_agent
        submit_event = chat_input.submit(
            fn=chat_handler,
            inputs=chat_submit_inputs,
            outputs=chat_submit_outputs,
        )
        send_event = send_btn.click(
            fn=chat_handler,
            inputs=chat_submit_inputs,
            outputs=chat_submit_outputs,
        )
        stop_btn.click(fn=None, cancels=[submit_event, send_event])
        new_chat_btn.click(
            fn=start_new_chat,
            inputs=[user_state, language_dropdown, show_english],
            outputs=[session_state, chat_picker, chatbot],
        )
        chat_picker.change(
            fn=load_selected_chat,
            inputs=[chat_picker, user_state],
            outputs=[session_state, chat_picker, chatbot, language_dropdown, show_english],
        )

    # ── Tab 2: Voice ───────────────────────────────────────────────────────
    with gr.Tab("🎤 Voice Assistant"):
        gr.Markdown(
            "### 🎤 Speak your question — get a voice reply!\n"
            "Supports Hindi, English, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada."
        )

        with gr.Row():
            with gr.Column(scale=1):
                voice_lang = gr.Dropdown(
                    choices=LANG_CHOICES,
                    value="hi-IN",
                    label="🌐 Your Language (for speech recognition)",
                )
                mic_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="🎙️ Record your question",
                )
                voice_btn = gr.Button("🚀 Send Voice Message", variant="primary", size="lg")
                gr.HTML('<p class="voice-hint">Tip: Click the mic, speak clearly, click stop, then press Send.</p>')

            with gr.Column(scale=1):
                transcript_box = gr.Textbox(
                    label="📝 What we heard (transcript)",
                    interactive=False,
                    lines=2,
                )
                reply_box = gr.Markdown(label="🤖 Agent Reply")
                audio_output = gr.Audio(
                    label="🔊 Voice Reply — press play",
                    type="filepath",
                    autoplay=True,
                )

        voice_btn.click(
            fn=handle_voice,
            inputs=[mic_input, voice_lang, user_state, session_state, language_dropdown, show_english],
            outputs=[transcript_box, reply_box, audio_output, session_state, chat_picker, usage_status],
        )

    with gr.Tab("Near me"):
        with gr.Row():
            nearby_city = gr.Textbox(label="City or area (if location is unavailable)")
            nearby_kind = gr.Dropdown(
                choices=[("Attractions", "attractions"), ("Restaurants", "restaurants"),
                         ("ATMs", "atm"), ("Restrooms", "restrooms"),
                         ("Petrol", "petrol"), ("Pharmacies", "pharmacy")],
                value="attractions", label="Category",
            )
        with gr.Row():
            nearby_open = gr.Checkbox(label="Open now")
            nearby_veg = gr.Checkbox(label="Vegetarian food only")
            nearby_rating = gr.Slider(0, 5, value=0, step=0.5, label="Minimum rating")
        nearby_latitude = gr.Textbox(visible=False)
        nearby_longitude = gr.Textbox(visible=False)
        nearby_find = gr.Button("Find nearby", variant="primary")
        nearby_results = gr.Markdown()

    with gr.Tab("Map"):
        with gr.Row():
            map_trip_picker = gr.Dropdown(choices=[], label="Saved trip", scale=3)
            map_day_picker = gr.Dropdown(choices=[("All days", "all")], value="all", label="Day")
            map_refresh = gr.Button("Refresh trips")
        map_status = gr.Markdown()
        map_canvas = gr.HTML()
        map_refresh.click(fn=refresh_map_trips_ui, inputs=[user_state], outputs=[map_trip_picker])
        map_trip_picker.change(
            fn=show_trip_map_ui, inputs=[map_trip_picker, map_day_picker, user_state],
            outputs=[map_canvas, map_status, map_day_picker],
        )
        map_day_picker.change(
            fn=show_trip_map_ui, inputs=[map_trip_picker, map_day_picker, user_state],
            outputs=[map_canvas, map_status, map_day_picker],
        )

    with gr.Tab("Phrasebook"):
        with gr.Row():
            phrase_situation = gr.Dropdown(
                choices=[("Restaurant", "restaurant"), ("Taxi", "taxi"), ("Hotel", "hotel"),
                         ("Bargaining", "bargaining"), ("Hospital", "hospital"),
                         ("Directions", "directions")], value="restaurant", label="Situation")
            phrase_language = gr.Dropdown(choices=LANG_CHOICES, value="hi-IN", label="Language")
            phrase_show = gr.Button("Show phrase", variant="primary")
        phrase_text = gr.Markdown()
        phrase_audio = gr.Audio(label="Phrase audio", type="filepath", interactive=False)
        phrase_show.click(fn=phrasebook_ui, inputs=[phrase_situation, phrase_language],
                          outputs=[phrase_text, phrase_audio])

    with gr.Tab("Live translation"):
        with gr.Row():
            live_a_language = gr.Dropdown(
                choices=[("Auto detect", "auto"), *LANG_CHOICES],
                value="hi-IN", label="Person A language")
            live_b_language = gr.Dropdown(choices=LANG_CHOICES, value="en-IN",
                                          label="Person B language")
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Person A")
                live_a_audio = gr.Audio(sources=["microphone"], type="filepath", label="Speak")
                live_a_text = gr.Textbox(label="Or type", max_lines=2)
                live_a_send = gr.Button("Translate A → B", variant="primary")
            with gr.Column():
                gr.Markdown("### Person B")
                live_b_audio = gr.Audio(sources=["microphone"], type="filepath", label="Speak")
                live_b_text = gr.Textbox(label="Or type", max_lines=2)
                live_b_send = gr.Button("Translate B → A", variant="primary")
        live_original = gr.Textbox(label="Original", interactive=False)
        live_translated = gr.Textbox(label="Translation", interactive=False)
        live_audio_out = gr.Audio(label="Spoken translation", type="filepath", autoplay=False)
        live_status = gr.Markdown()
        live_history_view = gr.Markdown()
        live_outputs = [live_original, live_translated, live_audio_out,
                        live_translation_state, live_status, live_history_view]
        live_a_send.click(
            fn=live_translate_a_ui,
            inputs=[live_a_audio, live_a_text, live_a_language, live_b_language,
                    live_translation_state, user_state], outputs=live_outputs,
        )
        live_b_send.click(
            fn=live_translate_b_ui,
            inputs=[live_b_audio, live_b_text, live_a_language, live_b_language,
                    live_translation_state, user_state], outputs=live_outputs,
        )

    with gr.Tab("Settings"):
        gr.Markdown("## Traveler profile")
        with gr.Row():
            profile_interests = gr.Textbox(label="Interests", placeholder="heritage, food, nature")
            profile_diet = gr.Dropdown(
                choices=[("No preference", ""), ("Vegetarian", "veg"), ("Vegan", "vegan"),
                         ("Jain", "jain"), ("Halal", "halal"), ("No restriction", "no_restriction")],
                value="", label="Diet",
            )
            profile_allergies = gr.Textbox(label="Allergies")
        with gr.Row():
            profile_budget = gr.Textbox(label="Budget range")
            profile_mobility = gr.Textbox(label="Mobility needs")
            profile_languages = gr.Textbox(label="Languages")
        with gr.Row():
            profile_home = gr.Textbox(label="Home city")
            profile_style = gr.Textbox(label="Travel style")
        with gr.Row():
            profile_save_btn = gr.Button("Save profile", variant="primary")
            profile_delete_btn = gr.Button("Delete profile", variant="stop")
        profile_status = gr.Markdown()
        profile_fields = [profile_interests, profile_diet, profile_allergies,
                          profile_budget, profile_mobility, profile_languages,
                          profile_home, profile_style]
        profile_save_btn.click(
            fn=save_profile_ui,
            inputs=[*profile_fields, user_state], outputs=[profile_status],
        )
        profile_delete_btn.click(
            fn=delete_profile_ui,
            inputs=[user_state], outputs=[profile_status, *profile_fields],
        )

        gr.Markdown("## Trusted contacts")
        gr.Markdown(
            "I consent to storing these contacts in this app's local database. They are used only to prepare message links. "
            "This app never sends messages; you must tap WhatsApp or SMS to send."
        )
        contacts_listing = gr.Markdown("No trusted contacts saved.")
        with gr.Row():
            contact_name = gr.Textbox(label="Name", placeholder="Contact name", max_lines=1)
            contact_phone = gr.Textbox(label="Phone", placeholder="+919876543210 (include country code)", max_lines=1)
        contact_consent = gr.Checkbox(label="I agree to save this contact", value=False)
        with gr.Row():
            add_contact_btn = gr.Button("Add contact", variant="primary")
            contact_to_delete = gr.Dropdown(choices=[], label="Contact to delete", scale=2)
            delete_contact_btn = gr.Button("Delete contact", variant="stop")
        contacts_status = gr.Markdown()
        contact_outputs = [contacts_status, contact_to_delete, share_contact, contacts_listing]

    with gr.Tab("Saved trips"):
        with gr.Row():
            saved_trip_picker = gr.Dropdown(choices=[], label="Trips", scale=4)
            saved_trips_refresh = gr.Button("Refresh")
        saved_trip_view = gr.Markdown()
        with gr.Row():
            saved_trip_title = gr.Textbox(label="Trip name", scale=4)
            saved_trip_rename = gr.Button("Rename")
            saved_trip_duplicate = gr.Button("Duplicate")
            saved_trip_delete = gr.Button("Delete", variant="stop")
        saved_trip_status = gr.Markdown()
        gr.Markdown("## Favorite places")
        favorites_listing = gr.Markdown("No favorite places saved.")
        with gr.Row():
            favorite_place = gr.Textbox(label="Place")
            favorite_source = gr.Textbox(label="Source URL (optional)")
            favorite_add = gr.Button("★ Save")
            favorite_remove = gr.Button("Remove")
        favorite_status = gr.Markdown()

        saved_trips_refresh.click(
            fn=refresh_trips_ui, inputs=[user_state],
            outputs=[saved_trip_picker, favorites_listing],
        )
        saved_trip_picker.change(
            fn=show_saved_trip_ui, inputs=[saved_trip_picker, user_state],
            outputs=[saved_trip_view],
        )
        saved_trip_actions = [saved_trip_status, saved_trip_picker, saved_trip_view]
        saved_trip_rename.click(
            fn=rename_saved_trip_ui,
            inputs=[saved_trip_picker, saved_trip_title, user_state],
            outputs=saved_trip_actions,
        )
        saved_trip_duplicate.click(
            fn=duplicate_saved_trip_ui,
            inputs=[saved_trip_picker, user_state], outputs=saved_trip_actions,
        )
        saved_trip_delete.click(
            fn=delete_saved_trip_ui,
            inputs=[saved_trip_picker, user_state], outputs=saved_trip_actions,
        )
        favorite_add.click(
            fn=add_favorite_ui,
            inputs=[favorite_place, favorite_source, user_state],
            outputs=[favorite_status, favorites_listing],
        )
        favorite_remove.click(
            fn=remove_favorite_ui,
            inputs=[favorite_place, user_state],
            outputs=[favorite_status, favorites_listing],
        )

    with gr.Tab("Privacy"):
        gr.Markdown("## Account")
        with gr.Row():
            account_email = gr.Textbox(label="Email", max_lines=1)
            account_password = gr.Textbox(label="Password", type="password", max_lines=1)
        with gr.Row():
            register_btn = gr.Button("Create account")
            login_btn = gr.Button("Sign in", variant="primary")
            logout_btn = gr.Button("Sign out")
        account_status = gr.Markdown()
        gr.Markdown("## Consent")
        location_consent = gr.Checkbox(label="Allow browser location lookup", value=False)
        contacts_consent = gr.Checkbox(label="Allow trusted contacts to be stored", value=False)
        privacy_status = gr.Markdown()
        gr.Markdown("## Delete my data")
        delete_confirm = gr.Checkbox(label="Permanently delete my chats, trips, contacts and account")
        delete_data_btn = gr.Button("Delete all my data", variant="stop")

        account_outputs = [
            account_status, user_state, session_state, chat_picker, chatbot,
            contact_to_delete, share_contact, contacts_listing,
            language_dropdown, show_english, location_consent, contacts_consent,
            usage_status,
            *profile_fields,
            saved_trip_picker,
            favorites_listing,
            map_trip_picker,
            live_translation_state,
            live_history_view,
        ]
        register_btn.click(
            fn=register_ui,
            inputs=[account_email, account_password, user_state, session_state],
            outputs=account_outputs,
        )
        login_btn.click(
            fn=login_ui,
            inputs=[account_email, account_password, user_state, session_state],
            outputs=account_outputs,
        )
        logout_btn.click(
            fn=logout_ui,
            inputs=[user_state, session_state],
            outputs=account_outputs,
        )
        delete_data_btn.click(
            fn=delete_my_data_ui,
            inputs=[user_state, session_state, delete_confirm],
            outputs=account_outputs,
        )
        for consent_control in (location_consent, contacts_consent):
            consent_control.change(
                fn=save_privacy_ui,
                inputs=[location_consent, contacts_consent, user_state],
                outputs=[privacy_status],
                queue=False,
            )

    add_contact_btn.click(
        fn=save_trusted_contact,
        inputs=[contact_name, contact_phone, user_state, contact_consent, contacts_consent],
        outputs=contact_outputs,
        queue=False,
    )
    delete_contact_btn.click(
        fn=remove_trusted_contact,
        inputs=[contact_to_delete, user_state],
        outputs=contact_outputs,
        queue=False,
    )

    get_location_btn.click(
        fn=lookup_emergency_services,
        inputs=[sos_city, sos_latitude, sos_longitude, location_consent],
        outputs=[nearby_services, sos_latitude, sos_longitude],
        js="""(city, latitude, longitude, allowed) => new Promise(resolve => {
            if (!allowed || !navigator.geolocation) return resolve([city, "", "", allowed]);
            navigator.geolocation.getCurrentPosition(
                p => resolve([city, String(p.coords.latitude), String(p.coords.longitude), allowed]),
                () => resolve([city, "", "", allowed]),
                {enableHighAccuracy: true, timeout: 8000, maximumAge: 60000}
            );
        })""",
        queue=False,
    )

    nearby_find.click(
        fn=find_nearby_ui,
        inputs=[nearby_city, nearby_latitude, nearby_longitude, nearby_kind,
                nearby_open, nearby_veg, nearby_rating, location_consent],
        outputs=[nearby_results],
        js="""(city, lat, lng, kind, openNow, veg, rating, allowed) => new Promise(resolve => {
            if (!allowed || !navigator.geolocation) return resolve([city, '', '', kind, openNow, veg, rating, allowed]);
            navigator.geolocation.getCurrentPosition(
                p => resolve([city, String(p.coords.latitude), String(p.coords.longitude), kind, openNow, veg, rating, allowed]),
                () => resolve([city, '', '', kind, openNow, veg, rating, allowed]),
                {enableHighAccuracy: true, timeout: 8000, maximumAge: 60000}
            );
        })""",
    )

    demo.load(
        fn=initialize_session,
        inputs=[user_state, session_state],
        outputs=[
            user_state,
            session_state,
            chat_picker,
            chatbot,
            contact_to_delete,
            share_contact,
            contacts_listing,
            language_dropdown,
            show_english,
            location_consent,
            contacts_consent,
            usage_status,
            *profile_fields,
            saved_trip_picker,
            favorites_listing,
            map_trip_picker,
            live_translation_state,
            live_history_view,
        ],
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
