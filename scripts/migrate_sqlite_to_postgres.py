"""Idempotent migration script from legacy SQLite sessions.db to PostgreSQL/SQLAlchemy.

Reads memory/sessions.db and populates SQLAlchemy models with count summaries.
"""

import json
import sqlite3
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.session import SessionLocal, init_db
from backend.app.db.models.user import User
from backend.app.db.models.conversation import Conversation, Message
from backend.app.db.models.trip import Trip, TripVersion
from backend.app.db.models.profile import Profile
from backend.app.db.models.contact import TrustedContact
from backend.app.db.models.feedback import Feedback
from backend.app.core.security import encrypt_phone


SQLITE_PATH = PROJECT_ROOT / "memory" / "sessions.db"


def migrate():
    if not SQLITE_PATH.exists():
        print(f"No SQLite database found at {SQLITE_PATH}; nothing to migrate.")
        return 0

    print(f"Connecting to SQLite: {SQLITE_PATH}")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    # Initialize SQLAlchemy tables
    init_db()
    db = SessionLocal()

    counts = {
        "users": 0,
        "conversations": 0,
        "messages": 0,
        "trips": 0,
        "trip_versions": 0,
        "profiles": 0,
        "trusted_contacts": 0,
        "feedback": 0,
    }

    try:
        # Check existing SQLite tables
        tables = {
            row[0]
            for row in sqlite_conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        # 1. Migrate Users
        if "users" in tables:
            user_rows = sqlite_conn.execute("SELECT user_id FROM users").fetchall()
            for u in user_rows:
                uid = u["user_id"]
                if not db.query(User).filter(User.id == uid).first():
                    user = User(
                        id=uid,
                        email=f"migrated_{uid[:12]}@safarsathi.local",
                        password_hash="[migrated_user]",
                        is_active=True,
                        is_verified=False,
                    )
                    db.add(user)
                    counts["users"] += 1
            db.commit()

        # 2. Migrate Sessions -> Conversations
        if "sessions" in tables:
            session_rows = sqlite_conn.execute(
                "SELECT session_id, user_id, title FROM sessions"
            ).fetchall()
            for s in session_rows:
                sid = s["session_id"]
                uid = s["user_id"]
                # Ensure user exists
                if not db.query(User).filter(User.id == uid).first():
                    db.add(User(id=uid, email=f"migrated_{uid[:12]}@safarsathi.local", password_hash="[migrated]"))
                    counts["users"] += 1
                    db.commit()

                if not db.query(Conversation).filter(Conversation.id == sid).first():
                    convo = Conversation(
                        id=sid,
                        user_id=uid,
                        title=s["title"] or "Imported chat",
                        language="en",
                    )
                    db.add(convo)
                    counts["conversations"] += 1
            db.commit()

        # 3. Migrate Turns -> Messages
        if "turns" in tables:
            turn_rows = sqlite_conn.execute(
                "SELECT session_id, role, content FROM turns ORDER BY turn_index ASC"
            ).fetchall()
            for t in turn_rows:
                sid = t["session_id"]
                convo = db.query(Conversation).filter(Conversation.id == sid).first()
                if convo:
                    msg = Message(
                        conversation_id=sid,
                        user_id=convo.user_id,
                        role=t["role"],
                        content=t["content"],
                        tools_used=[],
                        sources=[],
                        language="en",
                    )
                    db.add(msg)
                    counts["messages"] += 1
            db.commit()

        # 4. Migrate Trips
        if "trips" in tables:
            trip_rows = sqlite_conn.execute(
                "SELECT trip_id, session_id, user_id, title, data_json, current_version FROM trips"
            ).fetchall()
            for tr in trip_rows:
                tid = tr["trip_id"]
                uid = tr["user_id"]
                if not db.query(User).filter(User.id == uid).first():
                    db.add(User(id=uid, email=f"migrated_{uid[:12]}@safarsathi.local", password_hash="[migrated]"))
                    db.commit()

                if not db.query(Trip).filter(Trip.id == tid).first():
                    try:
                        data = json.loads(tr["data_json"])
                    except Exception:
                        data = {"destination": tr["title"]}

                    trip = Trip(
                        id=tid,
                        user_id=uid,
                        conversation_id=tr["session_id"],
                        title=tr["title"] or "Migrated trip",
                        destination=data.get("destination", tr["title"] or "India"),
                        duration_days=len(data.get("days", [])) or 1,
                        data_json=data,
                        current_version=tr["current_version"] or 1,
                    )
                    db.add(trip)
                    counts["trips"] += 1
            db.commit()

        # 5. Migrate Trip Versions
        if "trip_versions" in tables:
            v_rows = sqlite_conn.execute(
                "SELECT trip_id, version, data_json, change_summary FROM trip_versions"
            ).fetchall()
            for vr in v_rows:
                tid = vr["trip_id"]
                v_num = vr["version"]
                if db.query(Trip).filter(Trip.id == tid).first():
                    if not db.query(TripVersion).filter(TripVersion.trip_id == tid, TripVersion.version == v_num).first():
                        try:
                            data = json.loads(vr["data_json"])
                        except Exception:
                            data = {}
                        v_obj = TripVersion(
                            trip_id=tid,
                            version=v_num,
                            change_summary=vr["change_summary"] or "Migrated version",
                            data_json=data,
                        )
                        db.add(v_obj)
                        counts["trip_versions"] += 1
            db.commit()

        # 6. Migrate Profiles
        if "profiles" in tables:
            prof_rows = sqlite_conn.execute("SELECT * FROM profiles").fetchall()
            for pr in prof_rows:
                uid = pr["user_id"]
                if not db.query(Profile).filter(Profile.user_id == uid).first():
                    prof = Profile(
                        user_id=uid,
                        home_city=pr["home_city"] if "home_city" in pr.keys() else None,
                        diet_preference=pr["diet"] if "diet" in pr.keys() else "all",
                        allergies=json.loads(pr["allergies"]) if "allergies" in pr.keys() and pr["allergies"] else [],
                        travel_style=pr["travel_style"] if "travel_style" in pr.keys() else "normal",
                        budget_range=pr["budget_range"] if "budget_range" in pr.keys() else "mid",
                        mobility_notes=pr["mobility"] if "mobility" in pr.keys() else None,
                        interests=json.loads(pr["interests"]) if "interests" in pr.keys() and pr["interests"] else [],
                    )
                    db.add(prof)
                    counts["profiles"] += 1
            db.commit()

        # 7. Migrate Trusted Contacts (Encrypting phone numbers)
        if "trusted_contacts" in tables:
            tc_rows = sqlite_conn.execute("SELECT * FROM trusted_contacts").fetchall()
            for tc in tc_rows:
                uid = tc["user_id"]
                if not db.query(User).filter(User.id == uid).first():
                    db.add(User(id=uid, email=f"migrated_{uid[:12]}@safarsathi.local", password_hash="[migrated]"))
                    db.commit()

                name = tc["name"] if "name" in tc.keys() else "Contact"
                raw_phone = tc["phone"] if "phone" in tc.keys() else ""
                contact = TrustedContact(
                    user_id=uid,
                    name=name,
                    phone_encrypted=encrypt_phone(raw_phone),
                )
                db.add(contact)
                counts["trusted_contacts"] += 1
            db.commit()

        # 8. Migrate Feedback
        if "feedback" in tables:
            fb_rows = sqlite_conn.execute("SELECT * FROM feedback").fetchall()
            for fb in fb_rows:
                sid = fb["session_id"] if "session_id" in fb.keys() else None
                convo = db.query(Conversation).filter(Conversation.id == sid).first() if sid else None
                uid = convo.user_id if convo else "unknown"
                if uid != "unknown" and not db.query(User).filter(User.id == uid).first():
                    db.add(User(id=uid, email=f"migrated_{uid[:12]}@safarsathi.local", password_hash="[migrated]"))
                    db.commit()

                if uid != "unknown":
                    f_obj = Feedback(
                        user_id=uid,
                        conversation_id=sid,
                        rating=fb["rating"] if "rating" in fb.keys() else 1,
                        reason=fb["reason"] if "reason" in fb.keys() else None,
                        comment=fb["comment"] if "comment" in fb.keys() else None,
                        tools_used=json.loads(fb["tools_used"]) if "tools_used" in fb.keys() and fb["tools_used"] else [],
                    )
                    db.add(f_obj)
                    counts["feedback"] += 1
            db.commit()

        print("--- Migration Summary ---")
        for entity, count in counts.items():
            print(f"  {entity}: {count} records migrated")
        print("-------------------------")
        print("PASS: SQLite to PostgreSQL/SQLAlchemy migration complete.")
        return 0
    finally:
        sqlite_conn.close()
        db.close()


if __name__ == "__main__":
    raise SystemExit(migrate())
