"""Smoke test for Phase 2 Step F3: FastAPI API Layer (Chat SSE, Conversations, Trips, Voice, Emergency)."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.core.rate_limit import reset_rate_limits
from backend.app.db.base import Base
from backend.app.main import app


def main():
    reset_rate_limits()
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    checks = []

    # 1. Health & Emergency
    h_res = client.get("/api/v1/health")
    checks.append(("health endpoint responds", h_res.status_code == 200 and h_res.json()["status"] == "ok"))

    e_res = client.get("/api/v1/emergency")
    checks.append(("emergency returns numbers", e_res.status_code == 200 and "emergency_numbers" in e_res.json()))

    # 2. Authentication setup
    email = "f3_tester@safarsathi.test"
    pw = "F3Password123"
    client.post("/api/v1/auth/signup", json={"email": email, "password": pw})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    checks.append(("authenticated for API testing", login_res.status_code == 200))

    # 3. Create conversation & search
    convo_res = client.post("/api/v1/chat/conversations", json={"title": "Varanasi Tour", "language": "hi"})
    checks.append(("conversation created", convo_res.status_code == 201))
    convo_id = convo_res.json()["id"]

    # 4. SSE Chat Stream
    stream_res = client.post(
        "/api/v1/chat",
        json={"conversation_id": convo_id, "message": "Varanasi me kya dekhein?"},
    )
    checks.append(("chat SSE endpoint streams content", stream_res.status_code == 200 and "text/event-stream" in stream_res.headers["content-type"]))
    checks.append(("chat stream contains events", "event: " in stream_res.text))

    # 5. Conversation history
    history_res = client.get(f"/api/v1/chat/conversations/{convo_id}")
    checks.append(("conversation history retrieved with messages", history_res.status_code == 200 and history_res.json()["total_messages"] >= 2))

    # 6. Trips CRUD & Export
    trip_res = client.post(
        "/api/v1/trips",
        json={"title": "Varanasi Spiritual", "data": {"destination": "Varanasi", "days": [{"day": 1, "slots": [{"place": "Kashi Vishwanath"}]}]}},
    )
    checks.append(("trip saved", trip_res.status_code == 201))
    trip_id = trip_res.json()["id"]

    export_res = client.post(f"/api/v1/trips/{trip_id}/export", json={"format_type": "text"})
    checks.append(("trip export succeeds", export_res.status_code == 200 and "text" in export_res.json()))

    # 7. Profile & Contacts
    prof_res = client.put("/api/v1/profile", json={"home_city": "Kolkata", "diet_preference": "veg"})
    checks.append(("profile updated", prof_res.status_code == 200))

    contact_res = client.post("/api/v1/profile/contacts", json={"name": "Brother", "phone": "+91 9123456780"})
    checks.append(("trusted contact added", contact_res.status_code == 201))

    # 8. Feedback
    fb_res = client.post("/api/v1/feedback", json={"rating": 1, "comment": "Helpful"})
    checks.append(("feedback turn recorded", fb_res.status_code == 201))

    # Cleanup
    app.dependency_overrides.clear()

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
