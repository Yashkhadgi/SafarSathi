"""Smoke test for SafarSathi Step R2 (Chat-First UI Cards, SSE streaming, and persistence)."""

import json
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import SessionLocal, init_db
from backend.app.db.models.conversation import Conversation, Message
from backend.app.repositories.chat_repo import save_message, get_messages
from tools.itinerary_tool import build_itinerary
from tools.budget_tool import compare_budget_tiers
from tools.safety_tool import get_area_safety

def main():
    print("=== SafarSathi Step R2 Smoke Test ===")
    init_db()
    client = TestClient(app)

    # 1. Verify Tools emit UI payloads
    print("1. Testing tool UI card emission...")
    from memory.session_memory import create_session
    sess_id = create_session("smoke_user_r2", "Test chat")

    sample_places = [
        {"name": "Hawa Mahal", "source_name": "Rajasthan Tourism", "source_url": "https://tourism.rajasthan.gov.in", "last_verified": "2024-10"},
        {"name": "Amer Fort", "source_name": "Rajasthan Tourism", "source_url": "https://tourism.rajasthan.gov.in", "last_verified": "2024-10"},
        {"name": "City Palace", "source_name": "Rajasthan Tourism", "source_url": "https://tourism.rajasthan.gov.in", "last_verified": "2024-10"},
    ]
    itin = build_itinerary("Jaipur", 1, travelers=2, pace="relaxed", session_id=sess_id, places=sample_places)
    print("itin result:", itin)
    assert "ui" in itin, f"Itinerary missing 'ui' key: {itin.keys()}"
    assert itin["ui"]["type"] == "itinerary"
    print("PASS: Itinerary tool emits ui card payload")

    budget = compare_budget_tiers({"destination": "Jaipur", "duration_days": 3}, 2)
    print("budget result:", budget)
    assert "ui" in budget, f"Budget comparison missing 'ui' key: {budget.keys()}"
    assert budget["ui"]["type"] == "budget"
    print("PASS: Budget tier comparison emits ui card payload")

    sos = get_area_safety("Jaipur")
    assert "ui" in sos, f"Safety missing 'ui' key: {sos.keys()}"
    assert sos["ui"]["type"] == "sos"
    print("PASS: Area safety emits ui card payload")

    # 2. Verify Database Cards Column & History Persistence
    print("2. Testing Message cards persistence in database...")
    db = SessionLocal()
    try:
        # Create user via auth endpoint
        client.post("/api/v1/auth/signup", json={"email": "r2_tester@safarsathi.test", "password": "SafarSathi_R2_Pass123!"})
        login_res = client.post("/api/v1/auth/login", json={"email": "r2_tester@safarsathi.test", "password": "SafarSathi_R2_Pass123!"})
        assert login_res.status_code == 200
        user_id = login_res.json()["user"]["id"]

        convo = Conversation(user_id=user_id, title="R2 Card Test")
        db.add(convo)
        db.commit()

        # Save assistant message with cards
        sample_card = {"type": "itinerary", "version": "1.0", "data": itin}
        msg = save_message(
            db=db,
            conversation_id=convo.id,
            user_id=user_id,
            role="assistant",
            content="Here is your 3-day Jaipur plan with cards.",
            cards=[sample_card],
        )
        db.commit()

        # Retrieve messages and verify cards persisted
        msgs, total = get_messages(db, convo.id, user_id)
        assert len(msgs) == 1
        assert msgs[0].cards is not None
        assert len(msgs[0].cards) == 1
        assert msgs[0].cards[0]["type"] == "itinerary"
        print("PASS: Message cards JSON column saved and reloaded accurately")

        # Test API endpoint returns cards
        r = client.get(f"/api/v1/chat/conversations/{convo.id}/messages")
        assert r.status_code == 200, f"Failed getting messages: {r.text}"
        res_data = r.json()
        assert len(res_data["messages"]) == 1
        assert len(res_data["messages"][0]["cards"]) == 1
        assert res_data["messages"][0]["cards"][0]["type"] == "itinerary"
        print("PASS: GET /chat/conversations/{id}/messages returns cards in API payload")

    finally:
        db.close()

    print("\n✅ All Step R2 smoke tests passed successfully!")

if __name__ == "__main__":
    main()
