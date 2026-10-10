"""Per-user trusted contacts and user-initiated message link generation."""

import re
from urllib.parse import quote

from memory import session_memory


def _ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trusted_contacts (
            contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)


def _normalize_phone(phone):
    value = re.sub(r"[\s().-]", "", str(phone or ""))
    if not re.fullmatch(r"\+[1-9]\d{7,14}", value):
        return None
    return value


def list_contacts(user_id):
    try:
        if not user_id:
            return []
        conn = session_memory._get_conn()
        try:
            _ensure_table(conn)
            session_memory.ensure_user(conn, user_id)
            rows = conn.execute(
                "SELECT contact_id, name, phone FROM trusted_contacts WHERE user_id = ? ORDER BY contact_id",
                (user_id,),
            ).fetchall()
            conn.commit()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    except Exception:
        return []


def add_contact(user_id, name, phone, consent=False):
    try:
        name = str(name or "").strip()[:80]
        phone = _normalize_phone(phone)
        if not user_id:
            return {"error": "User session is unavailable."}
        if not consent:
            return {"error": "Please confirm consent before saving a contact."}
        if not name:
            return {"error": "Enter a contact name."}
        if not phone:
            return {"error": "Enter a valid international phone number, including country code (for example +919876543210)."}

        conn = session_memory._get_conn()
        try:
            _ensure_table(conn)
            conn.execute("BEGIN IMMEDIATE")
            session_memory.ensure_user(conn, user_id)
            count = conn.execute(
                "SELECT COUNT(*) FROM trusted_contacts WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            if count >= 3:
                conn.rollback()
                return {"error": "You can save up to 3 trusted contacts."}
            cursor = conn.execute(
                "INSERT INTO trusted_contacts (user_id, name, phone, created_at) VALUES (?, ?, ?, ?)",
                (user_id, name, phone, session_memory._now()),
            )
            conn.commit()
            return {"contact_id": cursor.lastrowid, "name": name, "phone": phone}
        finally:
            conn.close()
    except Exception as exc:
        return {"error": f"Could not save contact: {exc}"}


def delete_contact(user_id, contact_id):
    try:
        if not user_id:
            return {"error": "User session is unavailable."}
        conn = session_memory._get_conn()
        try:
            _ensure_table(conn)
            cursor = conn.execute(
                "DELETE FROM trusted_contacts WHERE contact_id = ? AND user_id = ?",
                (int(contact_id), user_id),
            )
            conn.commit()
            if not cursor.rowcount:
                return {"error": "Contact not found."}
            return {"deleted": True}
        finally:
            conn.close()
    except Exception as exc:
        return {"error": f"Could not delete contact: {exc}"}


def create_share_links(user_id, contact_id, template, latitude, longitude):
    """Build prefilled links only; this function never sends a message."""
    try:
        contact_id = int(contact_id)
        lat, lng = float(latitude), float(longitude)
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return {"error": "Location coordinates are invalid."}
        if template not in ("safe", "help"):
            return {"error": "Choose a message template."}

        conn = session_memory._get_conn()
        try:
            _ensure_table(conn)
            contact = conn.execute(
                "SELECT name, phone FROM trusted_contacts WHERE contact_id = ? AND user_id = ?",
                (contact_id, user_id),
            ).fetchone()
        finally:
            conn.close()
        if not contact:
            return {"error": "Choose one of your saved contacts."}

        coords = f"{lat:.6f},{lng:.6f}"
        maps_url = f"https://maps.google.com/?q={coords}"
        lead = "I'm safe" if template == "safe" else "I need help"
        message = f"{lead}. My location: {maps_url}"
        encoded = quote(message, safe="")
        digits = contact["phone"].lstrip("+")
        return {
            "name": contact["name"],
            "message": message,
            "maps_url": maps_url,
            "whatsapp_url": f"https://wa.me/{digits}?text={encoded}",
            "sms_url": f"sms:{contact['phone']}?body={encoded}",
        }
    except Exception as exc:
        return {"error": f"Could not prepare message links: {exc}"}
