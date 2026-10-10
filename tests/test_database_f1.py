"""Unit tests for Phase 2 Step F1: Database, Cascade Delete, Encryption, and Ownership."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.base import Base
from backend.app.core.security import encrypt_phone, decrypt_phone
from backend.app.repositories import (
    create_user,
    delete_user,
    get_user_by_id,
    create_conversation,
    get_conversation,
    delete_conversation,
    save_message,
    get_messages,
    search_messages,
    create_trip,
    get_trip,
    save_trip_version,
    delete_trip,
    get_or_create_profile,
    update_profile,
    add_trusted_contact,
    list_trusted_contacts,
    delete_trusted_contact,
    create_feedback,
)


class TestDatabaseF1(unittest.TestCase):
    def setUp(self):
        # In-memory SQLite for isolated, fast unit tests
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_contact_encryption_at_rest(self):
        """Verify phone numbers are encrypted at rest and properly decrypted upon retrieval."""
        plain_phone = "+91 98765 43210"
        encrypted = encrypt_phone(plain_phone)
        self.assertNotEqual(plain_phone, encrypted)
        self.assertTrue(len(encrypted) > 20)

        decrypted = decrypt_phone(encrypted)
        self.assertEqual(plain_phone, decrypted)

        # In repository
        u1 = create_user(self.db, "encrypt_test@example.com", "hash1")
        self.db.commit()

        contact = add_trusted_contact(self.db, u1.id, "Dr. Ramesh", plain_phone, "Doctor")
        self.db.commit()

        # Check DB model raw value is ciphertext
        self.assertNotEqual(plain_phone, contact.phone_encrypted)

        # Check repository list returns decrypted plain phone
        contact_list = list_trusted_contacts(self.db, u1.id)
        self.assertEqual(len(contact_list), 1)
        self.assertEqual(contact_list[0]["phone"], plain_phone)
        self.assertEqual(contact_list[0]["name"], "Dr. Ramesh")

    def test_ownership_enforcement_across_users(self):
        """Verify User A cannot access, view, or modify User B's resources."""
        user_a = create_user(self.db, "user_a@example.com", "hashA")
        user_b = create_user(self.db, "user_b@example.com", "hashB")
        self.db.commit()

        # 1. Conversations ownership
        convo_a = create_conversation(self.db, user_a.id, "User A Private Trip")
        self.db.commit()

        # User B cannot retrieve User A's conversation
        self.assertIsNone(get_conversation(self.db, convo_a.id, user_b.id))
        self.assertIsNotNone(get_conversation(self.db, convo_a.id, user_a.id))

        # User B cannot delete User A's conversation
        self.assertFalse(delete_conversation(self.db, convo_a.id, user_b.id))

        # 2. Trips ownership
        trip_a = create_trip(self.db, user_a.id, {"destination": "Jaipur", "days": []})
        self.db.commit()

        # User B cannot get or delete User A's trip
        self.assertIsNone(get_trip(self.db, trip_a.id, user_b.id))
        self.assertIsNotNone(get_trip(self.db, trip_a.id, user_a.id))
        self.assertFalse(delete_trip(self.db, trip_a.id, user_b.id))

        # 3. Contacts ownership
        contact_a = add_trusted_contact(self.db, user_a.id, "Sister", "+91 99999 11111")
        self.db.commit()

        # User B cannot delete User A's contact
        self.assertFalse(delete_trusted_contact(self.db, contact_a.id, user_b.id))

    def test_cascade_deletion(self):
        """Deleting a User must automatically cascade delete all dependent data in one transaction."""
        user = create_user(self.db, "cascade_user@example.com", "hash1")
        self.db.commit()
        uid = user.id

        # Add profile
        update_profile(self.db, uid, home_city="Nagpur", diet_preference="veg")
        # Add conversation and messages
        convo = create_conversation(self.db, uid, "Nagpur Chat")
        save_message(self.db, convo.id, uid, "user", "Hello assistant")
        save_message(self.db, convo.id, uid, "assistant", "Hello traveler")
        # Add trip and version
        trip = create_trip(self.db, uid, {"destination": "Nagpur", "days": [{"day": 1}]})
        save_trip_version(self.db, trip.id, uid, {"destination": "Nagpur", "days": [{"day": 1}, {"day": 2}]}, "Added day 2")
        # Add contact
        add_trusted_contact(self.db, uid, "Emergency Contact", "+91 112")
        # Add feedback
        create_feedback(self.db, uid, rating=1, conversation_id=convo.id, comment="Great plan")
        self.db.commit()

        # Verify items exist
        self.assertIsNotNone(get_user_by_id(self.db, uid))
        self.assertIsNotNone(get_conversation(self.db, convo.id, uid))
        self.assertIsNotNone(get_trip(self.db, trip.id, uid))
        self.assertEqual(len(list_trusted_contacts(self.db, uid)), 1)

        # Delete user
        self.assertTrue(delete_user(self.db, uid))
        self.db.commit()

        # Verify user is gone
        self.assertIsNone(get_user_by_id(self.db, uid))
        # Verify dependent entities are deleted
        self.assertIsNone(get_conversation(self.db, convo.id, uid))
        self.assertIsNone(get_trip(self.db, trip.id, uid))
        self.assertEqual(len(list_trusted_contacts(self.db, uid)), 0)

    def test_chat_pagination_and_search(self):
        """Verify message pagination and search operations."""
        user = create_user(self.db, "chat_tester@example.com", "hash1")
        convo = create_conversation(self.db, user.id, "Delhi exploration")
        self.db.commit()

        for i in range(15):
            role = "user" if i % 2 == 0 else "assistant"
            content = f"Turn {i} mentioning Taj Mahal monument" if i == 7 else f"Turn {i} general message"
            save_message(self.db, convo.id, user.id, role, content)
        self.db.commit()

        # Pagination: 10 per page
        page1, total = get_messages(self.db, convo.id, user.id, limit=10, offset=0)
        self.assertEqual(total, 15)
        self.assertEqual(len(page1), 10)

        page2, _ = get_messages(self.db, convo.id, user.id, limit=10, offset=10)
        self.assertEqual(len(page2), 5)

        # Search
        results = search_messages(self.db, user.id, "Taj Mahal")
        self.assertEqual(len(results), 1)
        self.assertIn("Taj Mahal", results[0].content)


if __name__ == "__main__":
    unittest.main()
