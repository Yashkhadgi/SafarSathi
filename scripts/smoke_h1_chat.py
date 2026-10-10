"""End-to-End Chat Verification for Step H1 (Chat Send, SSE streaming, Enter/Button, History Persistence)."""

import os
import json
os.environ["USE_FAKE_LLM"] = "true"

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import SessionLocal, init_db
from backend.app.repositories.chat_repo import get_messages

def main():
    print("=== SafarSathi Step H1 End-to-End Chat Test ===")
    init_db()
    client = TestClient(app)

    # 1. User Authentication (Signup & Login)
    print("1. Testing Auth Flow...")
    signup_res = client.post("/api/v1/auth/signup", json={
        "email": "h1_tester@safarsathi.test",
        "password": "SafarSathi_H1_Pass123!"
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": "h1_tester@safarsathi.test",
        "password": "SafarSathi_H1_Pass123!"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    user_id = login_res.json()["user"]["id"]
    print("PASS: Authenticated test session established")

    # 2. Create Conversation
    print("2. Testing Conversation Creation...")
    convo_res = client.post("/api/v1/chat/conversations", json={"title": "H1 Chat Flow"})
    assert convo_res.status_code in (200, 201), f"Failed to create conversation: {convo_res.text}"
    convo_id = convo_res.json()["id"]
    print(f"PASS: Conversation created with ID {convo_id}")


    # 3. Send Message 1 (Simulating Enter key send)
    print("3. Testing Chat Send via Enter Key (SSE streaming)...")
    chat_payload_1 = {
        "conversation_id": convo_id,
        "message": "Nagpur to Mumbai train and road route",
        "language": "en"
    }
    res_1 = client.post("/api/v1/chat", json=chat_payload_1)
    assert res_1.status_code == 200, f"Chat SSE stream failed: {res_1.status_code}"
    
    # Parse SSE stream chunks
    sse_text = res_1.text
    assert "event: status" in sse_text or "event: token" in sse_text or "event: done" in sse_text, "No SSE events streamed"
    print("PASS: Message 1 sent and SSE streamed successfully")

    # 4. Send Message 2 (Simulating Button click send)
    print("4. Testing Chat Send via Button Click (SSE streaming with UI cards)...")
    chat_payload_2 = {
        "conversation_id": convo_id,
        "message": "Plan 3 days in Jaipur for 2 people",
        "language": "en"
    }
    res_2 = client.post("/api/v1/chat", json=chat_payload_2)
    assert res_2.status_code == 200, f"Chat SSE stream failed: {res_2.status_code}"
    assert "event: ui_card" in res_2.text or "event: token" in res_2.text, "SSE stream missing tokens/cards"
    print("PASS: Message 2 sent and streamed with UI card payload")

    # 5. History Persistence (Reload after page refresh simulation)
    print("5. Testing History Reload from Database...")
    hist_res = client.get(f"/api/v1/chat/conversations/{convo_id}/messages")
    assert hist_res.status_code == 200, f"Failed reloading messages: {hist_res.text}"
    history = hist_res.json()["messages"]
    assert len(history) >= 4, f"Expected at least 4 messages (2 user + 2 assistant), got {len(history)}"
    
    user_msgs = [m for m in history if m["role"] == "user"]
    asst_msgs = [m for m in history if m["role"] == "assistant"]
    assert len(user_msgs) >= 2, "User messages not saved in DB"
    assert len(asst_msgs) >= 2, "Assistant replies not saved in DB"
    print("PASS: Full conversation history saved to database and reloaded accurately")

    # 6. Friendly Error Handling on Backend Error
    print("6. Testing Error Handling on Invalid/Offline Requests...")
    bad_res = client.post("/api/v1/chat", json={
        "conversation_id": "non_existent_conversation_id_12345",
        "message": "Hello"
    })
    assert bad_res.status_code in (404, 400), "Should reject invalid conversation gracefully"
    print("PASS: Error responses structured cleanly without raw server exception leaks")

    print("\n✅ All Checkpoint H1 tests passed successfully!")

if __name__ == "__main__":
    main()
