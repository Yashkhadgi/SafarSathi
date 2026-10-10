"""Unit tests for Phase 2 Step F3: API Layer, Chat SSE, Trips, Profile, and Ownership."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.core.rate_limit import reset_rate_limits
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.db.models.user import User
from backend.app.main import app


class TestApiF3(unittest.TestCase):
    def setUp(self):
        reset_rate_limits()
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

    def _create_authenticated_client(self, email: str, password: str = "SecurePassword123") -> TestClient:
        client = TestClient(app)
        client.post("/api/v1/auth/signup", json={"email": email, "password": password})
        client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return client

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)

    def test_conversation_management_and_ownership(self):
        """Verify conversation creation, listing, renaming, deletion, and ownership enforcement."""
        client_a = self._create_authenticated_client("usera@safarsathi.test")
        client_b = self._create_authenticated_client("userb@safarsathi.test")

        # 1. User A creates conversation
        create_res = client_a.post(
            "/api/v1/chat/conversations",
            json={"title": "Rajasthan Heritage Trip", "language": "hi"},
        )
        self.assertEqual(create_res.status_code, 201)
        convo_id = create_res.json()["id"]

        # 2. User A can retrieve it
        get_res = client_a.get(f"/api/v1/chat/conversations/{convo_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["conversation"]["title"], "Rajasthan Heritage Trip")

        # 3. User B is DENIED access (404 / ownership isolation)
        b_res = client_b.get(f"/api/v1/chat/conversations/{convo_id}")
        self.assertEqual(b_res.status_code, 404)

        # 4. User B cannot rename User A's conversation
        b_rename = client_b.patch(
            f"/api/v1/chat/conversations/{convo_id}",
            json={"title": "Hacked Title"},
        )
        self.assertEqual(b_rename.status_code, 404)

        # 5. User A renames conversation
        a_rename = client_a.patch(
            f"/api/v1/chat/conversations/{convo_id}",
            json={"title": "Updated Rajasthan Tour"},
        )
        self.assertEqual(a_rename.status_code, 200)

        # 6. User B cannot delete User A's conversation
        b_del = client_b.delete(f"/api/v1/chat/conversations/{convo_id}")
        self.assertEqual(b_del.status_code, 404)

        # 7. User A deletes conversation
        a_del = client_a.delete(f"/api/v1/chat/conversations/{convo_id}")
        self.assertEqual(a_del.status_code, 200)

    def test_trip_crud_versioning_and_export(self):
        """Verify trip saving, version update, undo, and export."""
        client_a = self._create_authenticated_client("usera_trip@safarsathi.test")
        client_b = self._create_authenticated_client("userb_trip@safarsathi.test")

        trip_payload = {
            "title": "Goa Beach Vacation",
            "data": {
                "destination": "Goa",
                "days": [{"day": 1, "slots": [{"place": "Baga Beach"}]}],
            },
        }

        # 1. User A creates trip
        save_res = client_a.post("/api/v1/trips", json=trip_payload)
        self.assertEqual(save_res.status_code, 201)
        trip_id = save_res.json()["id"]

        # 2. User B cannot view User A's trip
        b_get = client_b.get(f"/api/v1/trips/{trip_id}")
        self.assertEqual(b_get.status_code, 404)

        # 3. Update trip -> Version 2
        update_payload = {
            "data": {
                "destination": "Goa",
                "days": [
                    {"day": 1, "slots": [{"place": "Baga Beach"}]},
                    {"day": 2, "slots": [{"place": "Fort Aguada"}]},
                ],
            },
            "change_summary": "Added Day 2 Aguada",
        }
        patch_res = client_a.patch(f"/api/v1/trips/{trip_id}", json=update_payload)
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["version"], 2)

        # 4. Undo trip -> Version 3 (reverts to Day 1 plan)
        undo_res = client_a.post(f"/api/v1/trips/{trip_id}/undo")
        self.assertEqual(undo_res.status_code, 200)
        self.assertEqual(len(undo_res.json()["data"]["days"]), 1)

        # 5. Export trip (WhatsApp text & .ics)
        exp_res = client_a.post(f"/api/v1/trips/{trip_id}/export", json={"format_type": "text"})
        self.assertEqual(exp_res.status_code, 200)
        self.assertIn("Goa", exp_res.json()["text"])

    def test_profile_and_contacts_limits(self):
        """Verify profile updates and max 3 trusted contacts limit."""
        client_a = self._create_authenticated_client("usera_prof@safarsathi.test")

        # 1. Update Profile
        p_res = client_a.put(
            "/api/v1/profile",
            json={"home_city": "Mumbai", "diet_preference": "jain", "travel_style": "relaxed"},
        )
        self.assertEqual(p_res.status_code, 200)

        # 2. Add Contacts (up to 3)
        c1 = client_a.post("/api/v1/profile/contacts", json={"name": "Mom", "phone": "+91 9876543210"})
        c2 = client_a.post("/api/v1/profile/contacts", json={"name": "Dad", "phone": "+91 9876543211"})
        c3 = client_a.post("/api/v1/profile/contacts", json={"name": "Friend", "phone": "+91 9876543212"})
        self.assertEqual(c1.status_code, 201)
        self.assertEqual(c2.status_code, 201)
        self.assertEqual(c3.status_code, 201)

        # 4th contact rejected
        c4 = client_a.post("/api/v1/profile/contacts", json={"name": "Extra", "phone": "+91 9876543213"})
        self.assertEqual(c4.status_code, 400)
        self.assertIn("Maximum 3", c4.json()["detail"])

    def test_feedback_submission(self):
        """Verify feedback turn submission."""
        client_a = self._create_authenticated_client("usera_fb@safarsathi.test")

        fb_res = client_a.post(
            "/api/v1/feedback",
            json={"rating": 1, "comment": "Excellent itinerary recommendation!"},
        )
        self.assertEqual(fb_res.status_code, 201)
        self.assertIn("feedback_id", fb_res.json())


if __name__ == "__main__":
    unittest.main()
