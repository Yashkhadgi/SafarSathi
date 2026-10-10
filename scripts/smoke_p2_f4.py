#!/usr/bin/env python3
"""Smoke test script for Phase 2 Step F4: Frontend Foundation, Design Rules, and Static Serving."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app


def run_smoke_f4():
    print("=== SafarSathi Phase 2 Step F4 Smoke Test ===")

    # 1. Run Design Rules Linter
    print("1. Running design rules linter...")
    res = subprocess.run(["./scripts/design_lint.sh"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAIL: design_lint.sh failed:\n{res.stdout}\n{res.stderr}")
        sys.exit(1)
    print("PASS: design_lint.sh passed with 0 violations")

    # 2. Check build artifacts
    dist_index = PROJECT_ROOT / "frontend" / "dist" / "index.html"
    if not dist_index.exists():
        print("FAIL: frontend/dist/index.html does not exist. Run npm run build first.")
        sys.exit(1)
    print("PASS: frontend/dist/index.html build artifact exists")

    # 3. Test FastAPI static fallback / SPA serving
    client = TestClient(app)
    
    spa_routes = ["/", "/login", "/signup", "/privacy", "/terms", "/verify-email"]
    for route in spa_routes:
        res = client.get(route)
        if res.status_code != 200:
            print(f"FAIL: route {route} returned status {res.status_code}")
            sys.exit(1)
        if "SafarSathi" not in res.text and "root" not in res.text:
            print(f"FAIL: route {route} did not return SPA index.html content")
            sys.exit(1)
    print("PASS: FastAPI SPA static fallback successfully serves HTML for client routes")

    # 4. Confirm API routes take precedence over SPA
    health_res = client.get("/api/v1/health")
    if health_res.status_code != 200 or health_res.json().get("status") != "ok":
        print("FAIL: /api/v1/health did not return JSON")
        sys.exit(1)
    print("PASS: API routes (/api/v1/*) correctly take precedence over SPA catch-all")

    print("\n✅ All Step F4 tests passed successfully!")


if __name__ == "__main__":
    run_smoke_f4()
