"""Unit tests for Phase 2 Step F2: Auth, Refresh Token Rotation, Lockout, and Account Management."""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.api.deps import get_db
from backend.app.core.rate_limit import clear_failed_attempts, reset_rate_limits
from backend.app.core.security import create_access_token, hash_password, hash_token, verify_access_token, verify_password
from backend.app.db.base import Base
from backend.app.db.models.user import EmailToken, User
from backend.app.main import app


from sqlalchemy.pool import StaticPool


class TestAuthF2(unittest.TestCase):
    def setUp(self):
        reset_rate_limits()
        # Isolated SQLite database with StaticPool for auth tests
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        Base.metadata.create_all(self.engine)
        self.TestingSession = sessionmaker(bind=self.engine)

        def override_get_db():
            db = self.TestingSession()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        clear_failed_attempts("login_fail_tester@safarsathi.test")

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)

    def test_password_hashing(self):
        """Verify PBKDF2/Argon2id password hashing and verification."""
        pw = "SecretP@ssw0rd2026"
        hashed = hash_password(pw)
        self.assertTrue(verify_password(pw, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_jwt_access_token_creation_and_expiry(self):
        """Verify JWT access tokens encode claims and expire properly."""
        token = create_access_token("user-uuid-1", "user@test.com", is_admin=False, expires_in_minutes=15)
        payload = verify_access_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "user-uuid-1")
        self.assertEqual(payload["email"], "user@test.com")

        # Expired token
        expired_token = create_access_token("user-uuid-1", "user@test.com", expires_in_minutes=-5)
        self.assertIsNone(verify_access_token(expired_token))

    def test_signup_verify_and_login_flow(self):
        """Test full signup, email verification, login with cookies, and get /me."""
        email = "traveler@safarsathi.test"
        password = "SecurePassword123"

        # 1. Signup
        signup_res = self.client.post("/api/v1/auth/signup", json={"email": email, "password": password})
        self.assertEqual(signup_res.status_code, 201)
        self.assertEqual(signup_res.json()["status"], "pending_verification")

        # Get verification token from DB
        db = self.TestingSession()
        token_obj = db.query(EmailToken).filter(EmailToken.token_type == "verify_email").first()
        self.assertIsNotNone(token_obj)
        user = db.query(User).filter(User.email == email).first()
        self.assertFalse(user.is_verified)

        # 2. Verify Email (simulate valid token)
        # Directly verify user for test
        user.is_verified = True
        db.commit()
        db.close()

        # 3. Login
        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("access_token", login_res.cookies)
        self.assertIn("refresh_token", login_res.cookies)

        # 4. Get /me with cookie
        me_res = self.client.get("/api/v1/auth/me", cookies=login_res.cookies)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["email"], email)

    def test_refresh_token_rotation(self):
        """Test refresh token rotation and ensure old refresh tokens are invalidated upon rotation."""
        email = "rotator@safarsathi.test"
        password = "Password12345"

        self.client.post("/api/v1/auth/signup", json={"email": email, "password": password})
        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        self.assertEqual(login_res.status_code, 200)

        old_refresh = login_res.cookies.get("refresh_token")
        self.assertIsNotNone(old_refresh)

        # 1. First refresh
        refresh_res = self.client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_refresh})
        self.assertEqual(refresh_res.status_code, 200)
        new_refresh = refresh_res.cookies.get("refresh_token")
        self.assertNotEqual(old_refresh, new_refresh)

        # 2. Replaying old refresh token must be rejected
        replay_res = self.client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_refresh})
        self.assertEqual(replay_res.status_code, 401)

    def test_lockout_on_consecutive_failed_logins(self):
        """Verify 5 failed login attempts trigger temporary lockout."""
        email = "lockout@safarsathi.test"
        self.client.post("/api/v1/auth/signup", json={"email": email, "password": "RealPassword123"})

        for _ in range(4):
            res = self.client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword"})
            self.assertEqual(res.status_code, 401)
            self.assertIn("Invalid email or password", res.json()["detail"])

        # 5th attempt triggers lockout
        res5 = self.client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword"})
        self.assertEqual(res5.status_code, 401)
        self.assertIn("locked", res5.json()["detail"].lower())

    def test_export_data_and_hard_account_deletion(self):
        """Verify data export and cascade delete account with password verification."""
        email = "delete_me@safarsathi.test"
        password = "PasswordToDelete123"

        self.client.post("/api/v1/auth/signup", json={"email": email, "password": password})
        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        cookies = login_res.cookies

        # Export data
        export_res = self.client.get("/api/v1/auth/export-data", cookies=cookies)
        self.assertEqual(export_res.status_code, 200)
        self.assertIn("user", export_res.json())
        self.assertIn("profile", export_res.json())

        # Wrong password deletion fails
        fail_del = self.client.request("DELETE", "/api/v1/auth/account", json={"password": "WrongPassword"}, cookies=cookies)
        self.assertEqual(fail_del.status_code, 400)

        # Correct password deletes account
        del_res = self.client.request("DELETE", "/api/v1/auth/account", json={"password": password}, cookies=cookies)
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["deleted"])

        # Cannot log in anymore
        login_again = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        self.assertEqual(login_again.status_code, 401)


if __name__ == "__main__":
    unittest.main()
