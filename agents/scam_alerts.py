"""Automatic attachment of source-backed scam notes to relevant travel answers."""

import re

from tools.scam_tool import get_scam_alerts, known_scam_cities


_TRIGGERS = (
    re.compile(r"\b(?:taxi|taxis|cab|cabs|autos?|auto[- ]?rickshaws?|rickshaws?|tuk[- ]?tuks?)\b", re.I),
    re.compile(r"\b(?:guide|guides|tour guide|sightseeing tour)\b", re.I),
    re.compile(r"\b(?:shopping|shop|market|carpet|jewell?ery|gemstones?)\b", re.I),
    re.compile(r"\bairport\b.{0,50}\b(?:transfers?|pickup|pick up|hotel|cab|taxi|ride)\b", re.I),
    re.compile(r"\b(?:transfers?|pickup|pick up|hotel|cab|taxi|ride)\b.{0,50}\bairport\b", re.I),
)


def _match_city(text):
    folded = str(text or "").casefold()
    for city in sorted(known_scam_cities(), key=len, reverse=True):
        if re.search(r"(?<!\w)" + re.escape(city.casefold()) + r"(?!\w)", folded):
            return city
    return ""


def auto_attach_scam_alerts(answer, user_message=""):
    """Append a short sourced alert section when the exchange involves a trigger category."""
    try:
        answer = str(answer or "")
        combined = f"{user_message or ''}\n{answer}"
        if not any(pattern.search(combined) for pattern in _TRIGGERS):
            return answer
        city = _match_city(combined)
        if not city:
            return answer
        result = get_scam_alerts(city, context=user_message)
        if result.get("error") or not result.get("markdown"):
            return answer
        return answer.rstrip() + "\n\n" + result["markdown"]
    except Exception:
        return str(answer or "")
