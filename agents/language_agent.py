"""Language detection and failure-safe input/output localization pipeline."""

import re


LANGUAGES = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "bn-IN": "Bengali",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "mr-IN": "Marathi",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "hinglish": "Hinglish",
}

_SARVAM_LANGUAGES = {code for code in LANGUAGES if code not in ("en-IN", "hinglish")}
_HINGLISH_WORDS = {
    "aap", "acha", "achha", "batao", "chahiye", "dekhna", "hai", "hain", "kaise",
    "kahan", "kaun", "kab", "kya", "kyun", "kitna", "kitne", "karo", "karna",
    "ke", "ki", "ko", "kya", "mein", "me", "mujhe", "nahi", "nahin", "se", "thoda",
    "yaar", "milega", "jaana", "jana", "hai?",
}
_LINK_RE = re.compile(r"\[[^\]]+\]\(https?://[^)\s]+\)|https?://[^\s)]+")
_DEVANAGARI_MARATHI = re.compile(r"(?:आहे|आहेत|काय|मला|मध्ये|कुठे|कसे|पाहिजे|करा)")


def _script_language(text):
    ranges = (
        ("bn-IN", 0x0980, 0x09FF),
        ("ta-IN", 0x0B80, 0x0BFF),
        ("te-IN", 0x0C00, 0x0C7F),
        ("gu-IN", 0x0A80, 0x0AFF),
        ("kn-IN", 0x0C80, 0x0CFF),
    )
    for code, start, end in ranges:
        if any(start <= ord(char) <= end for char in text):
            return code
    if any(0x0900 <= ord(char) <= 0x097F for char in text):
        return "mr-IN" if _DEVANAGARI_MARATHI.search(text) else "hi-IN"
    words = set(re.findall(r"[a-z]+", text.casefold()))
    if len(words & _HINGLISH_WORDS) >= 2:
        return "hinglish"
    if any(char.isalpha() for char in text):
        return "en-IN"
    return ""


def _llm_language_guess(text):
    try:
        from config.settings import RAG_MODEL, ANTHROPIC_API_KEY
        if not ANTHROPIC_API_KEY:
            return ""
        from tools.llm_wrapper import call_llm

        result = call_llm(
            model=RAG_MODEL,
            system_prompt=(
                "Identify the dominant language of the user text. Return exactly one of these codes: "
                "en-IN, hi-IN, bn-IN, ta-IN, te-IN, mr-IN, gu-IN, kn-IN, hinglish. "
                "Use hinglish for Hindi written in Latin letters mixed with English. No extra text."
            ),
            user_message=str(text or "")[:1500],
            max_tokens=12,
        ).strip().lower()
        match = re.search(r"\b(en-in|hi-in|bn-in|ta-in|te-in|mr-in|gu-in|kn-in|hinglish)\b", result)
        return match.group(1) if match else ""
    except Exception:
        return ""


def detect_language(text, preference="auto"):
    try:
        if preference in LANGUAGES and preference != "auto":
            return preference
        text = str(text or "")
        script = _script_language(text)
        if script in _SARVAM_LANGUAGES or script == "hinglish":
            return script
        guessed = _llm_language_guess(text)
        return guessed or script or "en-IN"
    except Exception:
        return "en-IN"


def _protect_links(text):
    links = []

    def replace(match):
        token = f"ZXQKEEPURL{len(links)}TOKENQXZ"
        links.append((token, match.group(0)))
        return token

    return _LINK_RE.sub(replace, str(text or "")), links


def _restore_links(text, links):
    output = str(text or "")
    for token, link in links:
        if token not in output:
            return None
        output = output.replace(token, link)
    return output


def _claude_translate(text, target_language):
    try:
        from config.settings import RAG_MODEL, ANTHROPIC_API_KEY
        if not ANTHROPIC_API_KEY:
            return ""
        from tools.llm_wrapper import call_llm

        target = LANGUAGES.get(target_language, target_language)
        if target_language == "hinglish":
            target = "conversational Hinglish written in Latin letters, naturally mixing Hindi and English"
        result = call_llm(
            model=RAG_MODEL,
            system_prompt=(
                f"Translate faithfully into {target}. Return only the translation. "
                "Do not answer questions or add explanations. Preserve placeholder tokens exactly."
            ),
            user_message=str(text or "")[:12000],
            max_tokens=2500,
        )
        if not result or result.startswith("Sorry, something went wrong"):
            return ""
        return result.strip()
    except Exception:
        return ""


def input_normalizer(text, language):
    original = str(text or "")
    try:
        if language == "en-IN" or not original.strip():
            return original
        protected, links = _protect_links(original)
        if language in _SARVAM_LANGUAGES:
            try:
                from tools.translation_tool import translate_text
                translated = translate_text(protected, target_lang_code="en-IN", source_lang_code=language)
            except Exception:
                translated = protected
            if translated and translated != protected:
                restored = _restore_links(translated, links)
                if restored is not None:
                    return restored
        translated = _claude_translate(protected, "en-IN")
        restored = _restore_links(translated, links) if translated else None
        return restored if restored is not None else original
    except Exception:
        return original


def output_localizer(text, language, show_english=False):
    original = str(text or "")
    try:
        if show_english or language == "en-IN" or language not in LANGUAGES:
            return original
        protected, links = _protect_links(original)
        translated = ""
        if language in _SARVAM_LANGUAGES:
            try:
                from tools.translation_tool import translate_text
                translated = translate_text(protected, target_lang_code=language, source_lang_code="en-IN")
            except Exception:
                translated = ""
        if not translated or translated == protected:
            translated = _claude_translate(protected, language)
        restored = _restore_links(translated, links) if translated else None
        return restored if restored is not None else original
    except Exception:
        return original


def run_language_pipeline(text, core_agent, preference="auto", show_english=False, previous_language=""):
    """Normalize input, invoke the core callable, and localize its answer."""
    input_language = detect_language(text)
    output_language = preference if preference in LANGUAGES else input_language
    if preference == "auto" and previous_language and input_language in ("en-IN", "hinglish"):
        # Keep short English follow-ups in the established conversation language.
        if len(str(text or "").split()) <= 8 and previous_language in LANGUAGES:
            output_language = previous_language
    normalized = input_normalizer(text, input_language)
    answer = core_agent(normalized)
    return output_localizer(answer, output_language, show_english), output_language
