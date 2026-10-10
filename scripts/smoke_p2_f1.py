"""Smoke test for Phase 2 Step F1: PostgreSQL / SQLAlchemy 2 Database & Repository Layer."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.session import init_db, SessionLocal, engine
from backend.app.core.security import encrypt_phone, decrypt_phone
from backend.app.repositories import (
    create_user,
    get_user_by_id,
    delete_user,
    create_conversation,
    get_conversation,
    save_message,
    get_messages,
    search_messages,
    create_trip,
    get_trip,
    save_trip_version,
    delete_trip,
    get_or_create_profile,
    update_profile,
    add_trusted_contact,
    list_trusted_contacts,
    delete_trusted_contact,
    create_feedback,
)


def main():
    checks = []

    # 1. Initialize DB tables
    try:
        init_db()
        checks.append(("SQLAlchemy 2 tables initialized", True))
    except Exception as exc:
        checks.append(("SQLAlchemy 2 tables initialized", False))
        print(f"FAIL: DB init error: {exc}")
        return 1

    db = SessionLocal()
    try:
        # 2. Contact encryption check
        raw_phone = "+91 91234 56789"
        encrypted = encrypt_phone(raw_phone)
        decrypted = decrypt_phone(encrypted)
        checks.append(("contact phone encrypted at rest", encrypted != raw_phone and len(encrypted) > 20))
        checks.append(("contact phone decrypts accurately", decrypted == raw_phone))

        # 3. Create users
        u1 = create_user(db, "smoke_user_1@safarsathi.test", "hash_pw1")
        u2 = create_user(db, "smoke_user_2@safarsathi.test", "hash_pw2")
        db.commit()
        checks.append(("users created with UUIDs", bool(u1.id and u2.id)))

        # 4. Conversation & Messages
        c1 = create_conversation(db, u1.id, "Delhi Heritage Tour")
        m1 = save_message(db, c1.id, u1.id, "user", "Tell me about Qutub Minar")
        m2 = save_message(db, c1.id, u1.id, "assistant", "Qutub Minar is a 73m minaret built in 1193.")
        db.commit()

        msgs, total = get_messages(db, c1.id, u1.id)
        checks.append(("messages saved and fetched", total == 2 and len(msgs) == 2))

        # Ownership check
        c_cross = get_conversation(db, c1.id, u2.id)
        checks.append(("cross-user conversation access denied", c_cross is None))

        # 5. Full-text search
        search_res = search_messages(db, u1.id, "Qutub Minar")
        checks.append(("message search finds keywords", len(search_res) >= 1))

        # 6. Trip and versioning
        trip = create_trip(db, u1.id, {"destination": "Delhi", "days": [{"day": 1}]})
        v2 = save_trip_version(db, trip.id, u1.id, {"destination": "Delhi", "days": [{"day": 1}, {"day": 2}]}, "Added Day 2")
        db.commit()

        checks.append(("trip created with version history", trip.current_version == 2))
        checks.append(("cross-user trip access denied", get_trip(db, trip.id, u2.id) is None))

        # 7. Trusted contacts with encryption
        contact = add_trusted_contact(db, u1.id, "Friend", raw_phone, "Travel Buddy")
        db.commit()
        clist = list_trusted_contacts(db, u1.id)
        checks.append(("trusted contact saved with encryption", len(clist) == 1 and clist[0]["phone"] == raw_phone))

        # 8. Cascade delete
        del_ok = delete_user(db, u1.id)
        db.commit()
        checks.append(("user delete cascades completely", del_ok and get_user_by_id(db, u1.id) is None))
        checks.append(("cascade deletes conversation", get_conversation(db, c1.id, u1.id) is None))
        checks.append(("cascade deletes trip", get_trip(db, trip.id, u1.id) is None))
        checks.append(("cascade deletes contacts", len(list_trusted_contacts(db, u1.id)) == 0))

        # Cleanup test user 2
        delete_user(db, u2.id)
        db.commit()

        for label, passed in checks:
            print(f"{'PASS' if passed else 'FAIL'}: {label}")

        return 0 if all(passed for _, passed in checks) else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
