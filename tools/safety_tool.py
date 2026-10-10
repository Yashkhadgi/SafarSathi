"""B8: Safety tool — area safety, medical help, and lost-document guidance.

IMPORTANT DISCLAIMERS embedded in all responses:
- No medicine dosages are ever provided.
- Medical content always recommends consulting a qualified doctor.
- Emergency numbers 108 (ambulance) and 112 (national emergency) are always included.
"""

import json
from pathlib import Path

_KB_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"

_EMERGENCY_FOOTER = (
    "\n\n⚠️ EMERGENCY: Dial 112 (national) or 108 (ambulance) immediately in any life-threatening situation. "
    "Tourist police helpline: 1363. This information is for general guidance only — always contact local authorities for help."
)

_MEDICAL_DISCLAIMER = (
    "\n\nDISCLAIMER: This is general orientation information only. "
    "Consult a qualified doctor for any medical advice, diagnosis, or treatment. "
    "Do NOT self-medicate. For emergencies call 108 or 112 immediately."
)

_LOST_DOCS_DISCLAIMER = (
    "\n\nDISCLAIMER: Official procedures may change — always verify with local police, "
    "the Passport Seva portal (passportindia.gov.in), or your country's embassy/consulate directly."
)


def _load_kb_records():
    """Load and return all knowledge base records. Returns empty list on failure."""
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


def _find_records(city: str, category: str):
    """Return KB records matching city and category (case-insensitive)."""
    records = _load_kb_records()
    city_lower = city.strip().casefold()
    results = []
    for rec in records:
        if (rec.get("category", "").casefold() == category.casefold()
                and rec.get("place", "").casefold() == city_lower):
            results.append(rec)
    return results


def get_area_safety(city: str, context: str = "") -> dict:
    """Return area safety information for a city.

    Args:
        city: City name to look up.
        context: Optional context like 'night', 'women_solo', 'ghat area'.

    Returns:
        dict with safety_tips, emergency_numbers, source, or error.
    """
    try:
        city = str(city or "").strip()
        if not city:
            return {"error": "City name is required"}

        records = _find_records(city, "area_safety")
        if not records:
            # Generic fallback
            return {
                "city": city,
                "safety_tips": (
                    f"No specific safety data found for {city} in our knowledge base. "
                    "General India travel advice: keep belongings secure, use app-based transport at night, "
                    "and use emergency number 112 when needed."
                ),
                "emergency_numbers": {"national_emergency": "112", "ambulance": "108", "tourist_police": "1363"},
                "source": "UK FCDO general India guidance",
                "source_url": "https://www.gov.uk/foreign-travel-advice/india/safety-and-security",
                "last_verified": "2024-10",
                "disclaimer": _EMERGENCY_FOOTER,
            }

        rec = records[0]
        text = rec.get("text", "")
        if context:
            text = f"[Context: {context}]\n\n" + text
        text += _EMERGENCY_FOOTER

        res = {
            "city": city,
            "safety_tips": text,
            "emergency_numbers": {"national_emergency": "112", "ambulance": "108", "tourist_police": "1363"},
            "source": rec.get("source_name", ""),
            "source_url": rec.get("source_url", ""),
            "last_verified": rec.get("last_verified", ""),
        }
        res["ui"] = {"type": "sos", "version": "1.0", "data": dict(res)}
        return res
    except Exception as exc:
        return {"error": f"Safety lookup failed: {exc}"}


def get_medical_help(symptom: str, city: str) -> dict:
    """Return medical facility info and general orientation for a symptom in a city.

    NOTE: No medicine dosages are provided. Always recommends seeing a doctor.

    Args:
        symptom: Reported symptom or concern (e.g., 'altitude sickness', 'fever', 'injury').
        city: City where the traveler is located.

    Returns:
        dict with nearby facilities, emergency numbers, and disclaimer.
    """
    try:
        city = str(city or "").strip()
        symptom = str(symptom or "").strip()
        if not city:
            return {"error": "City name is required"}

        records = _find_records(city, "medical_first_aid")

        altitude_cities = {"leh", "manali", "shimla", "darjeeling", "kedarnath", "badrinath"}
        altitude_note = ""
        if city.lower() in altitude_cities or "altitude" in symptom.lower() or "ams" in symptom.lower():
            altitude_note = (
                "\n\nALTITUDE SICKNESS (AMS) NOTE: If experiencing headache, nausea, dizziness or breathing difficulty "
                "at high altitude — rest, do NOT ascend further, hydrate, and descend if symptoms worsen. "
                "Seek medical attention immediately. Do NOT take medication without medical advice."
            )

        if not records:
            return {
                "city": city,
                "symptom": symptom,
                "guidance": (
                    f"No specific medical facility data in our knowledge base for {city}. "
                    "Dial 108 (ambulance) or 112 (national emergency) immediately for urgent help. "
                    "Search 'hospital near me' on Google Maps or ask your hotel front desk."
                ) + altitude_note + _MEDICAL_DISCLAIMER,
                "emergency_numbers": {"ambulance": "108", "national_emergency": "112"},
                "disclaimer": _MEDICAL_DISCLAIMER,
            }

        rec = records[0]
        guidance = rec.get("text", "") + altitude_note + _MEDICAL_DISCLAIMER

        return {
            "city": city,
            "symptom": symptom,
            "guidance": guidance,
            "emergency_numbers": {"ambulance": "108", "national_emergency": "112"},
            "source": rec.get("source_name", ""),
            "source_url": rec.get("source_url", ""),
            "last_verified": rec.get("last_verified", ""),
            "disclaimer": _MEDICAL_DISCLAIMER,
        }
    except Exception as exc:
        return {"error": f"Medical help lookup failed: {exc}"}


def get_lost_docs_help(what_lost: str, nationality: str = "Indian") -> dict:
    """Return guidance for lost documents while travelling.

    Args:
        what_lost: What was lost — e.g., 'passport', 'Aadhaar', 'PAN card', 'driving licence'.
        nationality: Traveler nationality, default 'Indian'.

    Returns:
        dict with step-by-step guidance and official contacts.
    """
    try:
        what_lost = str(what_lost or "").strip().lower()
        nationality = str(nationality or "Indian").strip()

        if not what_lost:
            return {"error": "Please specify what was lost (e.g., passport, Aadhaar, credit card)"}

        steps = []
        contacts = []

        # Step 1: Always police FIR
        steps.append("1. Go to nearest police station and file an FIR (First Information Report). Get a copy — you will need it for replacement.")

        if "passport" in what_lost:
            if nationality.lower() == "indian":
                steps.append("2. Visit the nearest Passport Seva Kendra (PSK) with your FIR, old passport copy (if available), and identity proof.")
                steps.append("3. Apply for a new/duplicate passport at passportindia.gov.in or visit PSK directly.")
                contacts.append({"name": "Passport Seva Portal", "url": "https://www.passportindia.gov.in/", "phone": "1800-258-1800 (toll-free)"})
            else:
                steps.append("2. Contact your country's embassy or consulate in India immediately for an Emergency Travel Document (ETD).")
                steps.append("3. Provide the FIR copy, passport-size photos, and proof of citizenship to your embassy.")
                contacts.append({"name": "Your country's embassy in India", "note": "Find via your government's official website"})
                contacts.append({"name": "Ministry of External Affairs (India) for assistance", "url": "https://www.mea.gov.in/"})

        if "aadhaar" in what_lost:
            steps.append("• For lost Aadhaar: Visit uidai.gov.in to download e-Aadhaar using your registered mobile number.")
            steps.append("• Or call UIDAI helpline 1947 (toll-free) for assistance.")
            contacts.append({"name": "UIDAI (Aadhaar)", "url": "https://uidai.gov.in/", "phone": "1947"})

        if "pan" in what_lost:
            steps.append("• For lost PAN card: Apply for a duplicate at incometax.gov.in or through NSDL/UTI portal.")
            contacts.append({"name": "Income Tax India (PAN)", "url": "https://www.incometax.gov.in/"})

        if "credit" in what_lost or "debit" in what_lost or "card" in what_lost:
            steps.append("• Immediately call your bank's 24-hour helpline to BLOCK the card. Most banks allow blocking via their mobile app too.")
            steps.append("• File an FIR if the card was stolen (not just lost).")

        if "driving" in what_lost or "licence" in what_lost or "license" in what_lost:
            steps.append("• For lost driving licence: Apply at your home state's Regional Transport Office (RTO) or Parivahan portal (parivahan.gov.in).")
            contacts.append({"name": "Parivahan (Driving Licence)", "url": "https://parivahan.gov.in/"})

        if "train" in what_lost or "railway" in what_lost or "ticket" in what_lost:
            steps.append("• For lost railway ticket: E-tickets are re-printable from irctc.co.in or IRCTC Rail Connect app. Physical ticket: apply at PRS counter with ID proof.")

        if not steps[1:]:
            # Generic other docs
            steps.append("2. Contact your hotel or travel company for assistance with identifying the relevant authority.")
            steps.append("3. Check with your travel insurance provider if you have coverage for document loss/replacement.")

        return {
            "what_lost": what_lost,
            "nationality": nationality,
            "steps": steps,
            "contacts": contacts,
            "emergency_numbers": {"national_emergency": "112", "police": "100"},
            "tourist_police_helpline": "1363",
            "tip": "Always keep digital scans of all documents in a secure cloud service (email, Google Drive) before and during travel.",
            "disclaimer": _LOST_DOCS_DISCLAIMER,
        }
    except Exception as exc:
        return {"error": f"Lost docs guidance failed: {exc}"}
