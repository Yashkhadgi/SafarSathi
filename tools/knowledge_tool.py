"""B11: Knowledge tool — food guide, temple guide, and etiquette lookups from KB."""

import json
from pathlib import Path

_KB_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"

_FOOD_ALLERGY_DISCLAIMER = (
    "\n\n⚠️ ALLERGY DISCLAIMER: Always inform restaurant staff of any food allergies. "
    "Cross-contamination can occur in shared kitchens. When in doubt, choose clearly labeled options."
)


def _load_kb_records():
    records = []
    try:
        for json_file in _KB_PATH.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        records.extend(data)
            except Exception:
                pass
    except Exception:
        pass
    return records


def _find_by_category_place(category: str, place: str = ""):
    records = _load_kb_records()
    results = []
    place_lower = place.strip().casefold()
    for rec in records:
        if rec.get("category", "").casefold() != category.casefold():
            continue
        if place_lower:
            rec_place = " ".join([rec.get("place", ""), rec.get("state", "")]).casefold()
            if place_lower not in rec_place:
                continue
        results.append(rec)
    return results


_VEG_KEYWORDS = {"veg", "vegetarian"}
_VEGAN_KEYWORDS = {"vegan"}
_JAIN_KEYWORDS = {"jain"}
_HALAL_KEYWORDS = {"halal", "muslim", "non-veg"}
_NONVEG_EXCLUDE = {"non_veg", "non-veg", "meat", "seafood", "fish"}


def _filter_food_text(text: str, tags: list, diet_filter: str) -> bool:
    """Return True if the record should be included given the diet filter."""
    diet_lower = (diet_filter or "").strip().casefold()
    if not diet_lower or diet_lower == "all":
        return True
    tag_str = " ".join(tags).casefold()
    if diet_lower in _VEG_KEYWORDS:
        # Exclude records tagged as non-veg only
        for kw in _NONVEG_EXCLUDE:
            if kw in tag_str and "veg" not in tag_str:
                return False
        return True
    if diet_lower in _VEGAN_KEYWORDS:
        return "vegan" in tag_str
    if diet_lower in _JAIN_KEYWORDS:
        return "jain" in tag_str
    if diet_lower in _HALAL_KEYWORDS:
        return "halal" in tag_str
    return True


def get_food_guide(city: str, diet_filter: str = "") -> dict:
    """Return food recommendations for a city with optional diet filter.

    Args:
        city: City name.
        diet_filter: Optional — 'veg', 'vegan', 'jain', 'halal', or '' for all.

    Returns:
        dict with food recommendations, diet note, and allergy disclaimer.
    """
    try:
        city = str(city or "").strip()
        diet_filter = str(diet_filter or "").strip().lower()
        if not city:
            return {"error": "City name is required"}

        records = _find_by_category_place("food_guide", city)

        if not records:
            return {
                "city": city,
                "diet_filter": diet_filter or "all",
                "info": f"No specific food guide data for {city} in our knowledge base. Try searching online for '{city} food guide'.",
                "disclaimer": _FOOD_ALLERGY_DISCLAIMER,
            }

        filtered = [r for r in records if _filter_food_text(r.get("text", ""), r.get("tags", []), diet_filter)]

        if not filtered:
            return {
                "city": city,
                "diet_filter": diet_filter,
                "info": f"No {diet_filter} food records found for {city}. Try a broader search.",
                "disclaimer": _FOOD_ALLERGY_DISCLAIMER,
            }

        result_texts = []
        sources = []
        for rec in filtered:
            result_texts.append(rec.get("text", ""))
            if rec.get("source_name"):
                sources.append({"name": rec["source_name"], "url": rec.get("source_url", "")})

        diet_note = ""
        if diet_filter in _VEG_KEYWORDS:
            diet_note = "🌿 Vegetarian filter applied. Note: many dishes use dairy (ghee, butter, paneer)."
        elif diet_filter in _VEGAN_KEYWORDS:
            diet_note = "🌱 Vegan filter applied. Confirm no dairy or eggs with the server — 'pure vegan' is not universally understood."
        elif diet_filter in _JAIN_KEYWORDS:
            diet_note = "🙏 Jain filter applied. Always confirm 'no onion, no garlic, no root vegetables' explicitly with the cook."
        elif diet_filter in _HALAL_KEYWORDS:
            diet_note = "☪️ Halal filter applied. Confirm halal certification with the restaurant."

        return {
            "city": city,
            "diet_filter": diet_filter or "all",
            "food_guide": "\n\n".join(result_texts) + _FOOD_ALLERGY_DISCLAIMER,
            "diet_note": diet_note,
            "sources": sources[:3],
        }
    except Exception as exc:
        return {"error": f"Food guide lookup failed: {exc}"}


def get_temple_guide(site_or_city: str) -> dict:
    """Return visiting guidelines for a temple or religious site.

    Args:
        site_or_city: Temple name, site name, or city.

    Returns:
        dict with visiting rules, dress code, and respectful conduct notes.
    """
    try:
        site_or_city = str(site_or_city or "").strip()
        if not site_or_city:
            return {"error": "Temple name or city name is required"}

        # Search both 'temple_guide' and 'etiquette' categories for religious sites
        records = []
        all_records = _load_kb_records()
        query_lower = site_or_city.casefold()
        for rec in all_records:
            if rec.get("category", "") not in ("temple_guide", "etiquette"):
                continue
            rec_text = " ".join([rec.get("place", ""), rec.get("state", ""), rec.get("text", "")]).casefold()
            if query_lower in rec_text:
                records.append(rec)

        if not records:
            return {
                "site_or_city": site_or_city,
                "info": (
                    f"No specific temple guide found for '{site_or_city}'. "
                    "General rules: remove shoes at entrance, dress modestly (cover shoulders and knees), "
                    "no photography inside sanctums, observe silence, and circumambulate clockwise."
                ),
            }

        texts = []
        sources = []
        for rec in records:
            texts.append(rec.get("text", ""))
            if rec.get("source_name"):
                sources.append({"name": rec["source_name"], "url": rec.get("source_url", "")})

        return {
            "site_or_city": site_or_city,
            "guide": "\n\n".join(texts),
            "sources": sources[:3],
        }
    except Exception as exc:
        return {"error": f"Temple guide lookup failed: {exc}"}


def get_etiquette(state_or_religion: str = "") -> dict:
    """Return cultural etiquette guidelines for a state or religious context.

    Args:
        state_or_religion: State name, religion, or '' for general India etiquette.

    Returns:
        dict with etiquette guidelines.
    """
    try:
        query = str(state_or_religion or "").strip()

        records = _find_by_category_place("etiquette", query)

        if not records:
            # Return general India record
            records = _find_by_category_place("etiquette", "India")

        if not records:
            return {
                "context": query or "general India",
                "guidelines": (
                    "General India etiquette: Remove shoes at religious sites. Dress modestly. "
                    "Use right hand for eating and giving items. Ask before photographing people. "
                    "Bargaining is normal in markets. Tip 10-15% at restaurants."
                ),
            }

        texts = []
        sources = []
        for rec in records:
            texts.append(rec.get("text", ""))
            if rec.get("source_name"):
                sources.append({"name": rec["source_name"], "url": rec.get("source_url", "")})

        return {
            "context": query or "general India",
            "guidelines": "\n\n".join(texts),
            "sources": sources[:3],
        }
    except Exception as exc:
        return {"error": f"Etiquette lookup failed: {exc}"}
