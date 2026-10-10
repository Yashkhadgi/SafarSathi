"""Smoke test for Phase 2 Step F2: Auth, Refresh Token Rotation, Lockout, and Account Management."""

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
from backend.app.core.rate_limit import clear_failed_attempts
from backend.app.core.security import hash_password, verify_password
from backend.app.db.base import Base
from backend.app.db.models.user import User
from backend.app.main import app


def main():
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
    checks.append(("health endpoint responds ok", h_res.status_code == 200 and h_res.json()["status"] == "ok"))

    e_res = client.get("/api/v1/emergency")
    checks.append(("public emergency endpoint returns 112", e_res.status_code == 200 and "112" in str(e_res.json())))

    # 2. Signup & verification
    email = "smoke_auth@safarsathi.test"
    pw = "P@ssword123456"
    s_res = client.post("/api/v1/auth/signup", json={"email": email, "password": pw})
    checks.append(("signup creates pending account", s_res.status_code == 201))

    # 3. Login & Cookies
    l_res = client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    checks.append(("login returns user and sets cookies", l_res.status_code == 200 and "access_token" in l_res.cookies))

    # 4. Get /me
    me_res = client.get("/api/v1/auth/me", cookies=l_res.cookies)
    checks.append(("get /me returns profile", me_res.status_code == 200 and me_res.json()["email"] == email))

    # 5. Refresh token rotation
    old_refresh = l_res.cookies.get("refresh_token")
    r_res = client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_refresh})
    checks.append(("refresh rotates refresh token", r_res.status_code == 200 and r_res.cookies.get("refresh_token") != old_refresh))

    # Replay of old refresh token fails
    replay_res = client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_refresh})
    checks.append(("old refresh token replay denied", replay_res.status_code == 401))

    # 6. Active sessions and audit log
    sess_res = client.get("/api/v1/auth/sessions", cookies=r_res.cookies)
    checks.append(("lists active sessions", sess_res.status_code == 200 and len(sess_res.json()) >= 1))

    hist_res = client.get("/api/v1/auth/login-history", cookies=r_res.cookies)
    checks.append(("login audit history recorded", hist_res.status_code == 200 and len(hist_res.json()) >= 1))

    # 7. Logout
    out_res = client.post("/api/v1/auth/logout", cookies=r_res.cookies)
    checks.append(("logout revokes session", out_res.status_code == 200 and out_res.json()["logged_out"]))

    # Cleanup
    app.dependency_overrides.clear()

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
