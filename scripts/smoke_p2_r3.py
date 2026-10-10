"""Smoke test for SafarSathi Step R3 (Chat-First Cards, Tools, and Settings)."""

import json
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import SessionLocal, init_db
from backend.app.db.models.conversation import Conversation, Message
from backend.app.repositories.chat_repo import save_message, get_messages

from tools.transport_tools import how_to_reach
from tools.realtime_tool import get_live_weather
from tools.phrasebook import phrase_for, emergency_phrase, get_all_phrases
from tools.entry_fees_tool import get_entry_fees
from tools.budget_ext_tool import check_fair_price
from tools.checklist_tool import smart_packing_list, pre_trip_checklist
from tools.optimizer_tool import optimize_route

def main():
    print("=== SafarSathi Step R3 Smoke Test ===")
    init_db()
    client = TestClient(app)

    # 1. Verify R3 Tools emit UI payloads
    print("1. Testing R3 Tool UI card emissions...")

    # route_options
    route = how_to_reach("Nagpur", "Mumbai")
    assert "ui" in route, f"Route missing 'ui': {route.keys()}"
    assert route["ui"]["type"] == "route_options"
    assert "options" in route["ui"]["data"]
    print("PASS: how_to_reach emits 'route_options' ui card")

    # phrasebook
    phrase = phrase_for("greeting", "hi")
    assert "ui" in phrase, f"Phrase missing 'ui': {phrase.keys()}"
    assert phrase["ui"]["type"] == "phrasebook"
    assert len(phrase["ui"]["data"]["phrases"]) > 0
    print("PASS: phrase_for emits 'phrasebook' ui card")

    # price_table (monument entry fees)
    fees = get_entry_fees("Jaipur")
    assert "ui" in fees, f"Entry fees missing 'ui': {fees.keys()}"
    assert fees["ui"]["type"] == "price_table"
    assert fees["ui"]["data"]["kind"] == "monument_entry"
    print("PASS: get_entry_fees emits 'price_table' ui card")

    # price_table (fair price transport)
    fair = check_fair_price("Mumbai")
    assert "ui" in fair, f"Fair price missing 'ui': {fair.keys()}"
    assert fair["ui"]["type"] == "price_table"
    print("PASS: check_fair_price emits 'price_table' ui card")

    # checklist (packing list)
    packing = smart_packing_list("Goa", 4, activities=["beach"], season="winter")
    assert "ui" in packing, f"Packing list missing 'ui': {packing.keys()}"
    assert packing["ui"]["type"] == "checklist"
    assert len(packing["ui"]["data"]["categories"]) > 0
    print("PASS: smart_packing_list emits 'checklist' ui card")

    # checklist (pre-trip checklist)
    pretrip = pre_trip_checklist("2026-11-15", "Kerala")
    assert "ui" in pretrip, f"Pre-trip missing 'ui': {pretrip.keys()}"
    assert pretrip["ui"]["type"] == "checklist"
    print("PASS: pre_trip_checklist emits 'checklist' ui card")

    # multi_city (TSP optimizer)
    multi = optimize_route(["Delhi", "Agra", "Jaipur"], origin="Delhi", total_days=6)
    assert "ui" in multi, f"Multi-city missing 'ui': {multi.keys()}"
    assert multi["ui"]["type"] == "multi_city"
    assert len(multi["ui"]["data"]["ordered_cities"]) == 3
    print("PASS: optimize_route emits 'multi_city' ui card")

    # 2. Verify Chat-first Settings & Profile endpoints
    print("2. Testing Profile & Trusted Contacts APIs for Chat-first Settings...")
    client.post("/api/v1/auth/signup", json={"email": "r3_tester@safarsathi.test", "password": "SafarSathi_R3_Pass123!"})
    login_res = client.post("/api/v1/auth/login", json={"email": "r3_tester@safarsathi.test", "password": "SafarSathi_R3_Pass123!"})
    assert login_res.status_code == 200

    # Profile update
    prof_res = client.put("/api/v1/profile", json={
        "home_city": "Nagpur",
        "diet_preference": "vegetarian",
        "allergies": ["peanuts"],
        "travel_style": "relaxed",
    })
    assert prof_res.status_code == 200
    assert prof_res.json()["profile"]["home_city"] == "Nagpur"
    print("PASS: Profile update in Settings works")

    # Trusted contacts CRUD
    c_res = client.post("/api/v1/profile/contacts", json={
        "name": "Family Member",
        "phone": "+919876543210",
        "relationship_label": "Emergency",
    })
    assert c_res.status_code == 201
    contact_id = c_res.json()["id"]
    print("PASS: Trusted contact creation works")

    # Get trusted contacts
    get_c = client.get("/api/v1/profile/contacts")
    assert get_c.status_code == 200
    assert len(get_c.json()) >= 1
    print("PASS: Trusted contacts list retrieval works")

    # Clean up contact
    del_c = client.delete(f"/api/v1/profile/contacts/{contact_id}")
    assert del_c.status_code in (200, 204)
    print("PASS: Trusted contact deletion works")


    print("\n✅ All Step R3 smoke tests passed successfully!")

if __name__ == "__main__":
    main()

