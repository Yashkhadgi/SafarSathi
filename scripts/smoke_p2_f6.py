"""Smoke test for SafarSathi Phase 2 Step F6 (P0 and P1 UI Screens & Tools API)."""

import os
from fastapi.testclient import TestClient
from backend.app.main import app

def main():
    print("=== SafarSathi Phase 2 Step F6 Smoke Test ===")
    client = TestClient(app)

    # 0. Authenticate
    test_email = "f6_tester@safarsathi.test"
    test_pass = "SafarSathi_P2_F6_Pass!"
    client.post("/api/v1/auth/signup", json={"email": test_email, "password": test_pass, "full_name": "F6 Tester"})
    login_res = client.post("/api/v1/auth/login", json={"email": test_email, "password": test_pass})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    print("PASS: Authenticated test client")

    # 1. Test P0 Tool Endpoints
    print("1. Testing P0 tools endpoints...")
    r = client.post("/api/v1/tools/itinerary/build", json={"origin": "Delhi", "destination": "Jaipur", "days": 3, "interests": ["heritage"]})
    assert r.status_code == 200, f"Failed itinerary build: {r.text}"
    itinerary = r.json()
    print("Itinerary result:", itinerary)
    assert isinstance(itinerary, dict)
    print("PASS: P0 itinerary build tool endpoint")

    r = client.post("/api/v1/tools/itinerary/edit", json={"itinerary": itinerary, "instruction": "Add Nahargarh Fort on Day 2 evening"})
    assert r.status_code == 200
    print("PASS: P0 itinerary edit patch tool endpoint")

    r = client.post("/api/v1/tools/budget/estimate", json={"origin": "Delhi", "destination": "Jaipur", "days": 3, "travelers": 2, "tier": "budget"})
    assert r.status_code == 200
    print("PASS: P0 budget tier estimator tool endpoint")

    r = client.get("/api/v1/tools/transport/reach?destination=Jaipur&origin=Delhi")
    assert r.status_code == 200
    print("PASS: P0 how-to-reach transport tool endpoint")

    # 2. Test P1 Tool Endpoints
    print("2. Testing P1 tools endpoints...")
    r = client.get("/api/v1/tools/safety/area?city=Jaipur")
    assert r.status_code == 200
    assert "safety" in r.json() or "general_tips" in r.json() or "city" in r.json()
    print("PASS: P1 area safety tool endpoint")

    r = client.get("/api/v1/tools/safety/medical?symptom=fever&city=Jaipur")
    assert r.status_code == 200
    print("PASS: P1 medical first-aid endpoint (no dosages)")

    r = client.get("/api/v1/tools/budget/entry-fees?place=Amer%20Fort")
    assert r.status_code == 200
    print("PASS: P1 monument entry fees tool endpoint")

    r = client.get("/api/v1/tools/budget/fair-prices?city=Jaipur")
    assert r.status_code == 200
    print("PASS: P1 fair pricing benchmarks tool endpoint")

    r = client.get("/api/v1/tools/knowledge/food?city=Jaipur&diet_filter=veg")
    assert r.status_code == 200
    print("PASS: P1 food guide with diet filter tool endpoint")

    r = client.get("/api/v1/tools/knowledge/temple?site_or_city=Jaipur")
    assert r.status_code == 200
    print("PASS: P1 temple etiquette tool endpoint")

    r = client.get("/api/v1/tools/recommender/destinations?budget_inr=15000&days=3&month=November&mood=heritage&origin_city=Delhi")
    assert r.status_code == 200
    print("PASS: P1 destination recommender tool endpoint")

    r = client.post("/api/v1/tools/optimizer/route", json=["Jaipur", "Agra"])
    assert r.status_code == 200
    print("PASS: P1 multi-city TSP optimizer tool endpoint")

    r = client.get("/api/v1/tools/checklist/packing?destination=Jaipur&days=3&season=winter")
    assert r.status_code == 200
    print("PASS: P1 packing checklist tool endpoint")

    r = client.get("/api/v1/tools/phrasebook")
    assert r.status_code == 200
    print("PASS: P1 phrasebook endpoint")

    print("\n✅ All Step F6 smoke tests passed successfully!")

if __name__ == "__main__":
    main()
