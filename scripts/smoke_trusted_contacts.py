"""Offline smoke checks for per-user trusted contacts and share links."""

import tempfile
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from memory import session_memory
from memory.trusted_contacts import add_contact, create_share_links, delete_contact, list_contacts


def main():
    original_path = session_memory.DB_PATH
    with tempfile.TemporaryDirectory() as directory:
        session_memory.DB_PATH = str(Path(directory) / "sessions.db")
        try:
            first = add_contact("user-a", "Alex", "+919876543210", True)
            print("PASS add contact" if "contact_id" in first else f"FAIL add contact: {first}")
            other_user_empty = not list_contacts("user-b")
            print("PASS user isolation" if other_user_empty else "FAIL user isolation")
            no_consent = add_contact("user-a", "No Consent", "+919876543211", False)
            consent_ok = "error" in no_consent and len(list_contacts("user-a")) == 1
            print("PASS consent required" if consent_ok else f"FAIL consent required: {no_consent}")
            second = add_contact("user-a", "Sam", "+919876543211", True)
            third = add_contact("user-a", "Lee", "+919876543212", True)
            fourth = add_contact("user-a", "Pat", "+919876543213", True)
            cap_ok = "contact_id" in second and "contact_id" in third and "error" in fourth
            print("PASS three-contact limit" if cap_ok else "FAIL three-contact limit")

            links = create_share_links("user-a", first.get("contact_id"), "help", 28.6139, 77.2090)
            link_ok = (
                "whatsapp_url" in links
                and links["whatsapp_url"].startswith("https://wa.me/919876543210?")
                and "https://maps.google.com/?q=28.613900,77.209000" in links.get("message", "")
                and links["sms_url"].startswith("sms:+919876543210?")
            )
            print("PASS prefilled links" if link_ok else f"FAIL prefilled links: {links}")

            deleted = delete_contact("user-a", first.get("contact_id"))
            for item in list_contacts("user-a"):
                delete_contact("user-a", item["contact_id"])
            delete_ok = deleted.get("deleted") and not list_contacts("user-a")
            print("PASS delete contact" if delete_ok else f"FAIL delete contact: {deleted}")
            if not ("contact_id" in first and other_user_empty and consent_ok and cap_ok and link_ok and delete_ok):
                return 1
            return 0
        finally:
            session_memory.DB_PATH = original_path


if __name__ == "__main__":
    raise SystemExit(main())
