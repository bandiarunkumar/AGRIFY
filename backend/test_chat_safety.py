"""Regression tests for AGRIFY Copilot request validation and safe fallback."""
import os
import unittest
from unittest.mock import patch

# Run from backend/: python -m unittest test_chat_safety.py
import api


class CopilotSafetyTests(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()
        self.key_patch = patch.dict(os.environ, {}, clear=False)
        self.key_patch.start()
        os.environ.pop("GEMINI_API_KEY", None)
        self.genai_patch = patch.object(api, "genai", None)
        self.genai_patch.start()

    def tearDown(self):
        self.genai_patch.stop()
        self.key_patch.stop()

    def test_non_object_json_is_rejected(self):
        response = self.client.post("/api/chat", json=["not", "an", "object"])
        self.assertEqual(response.status_code, 400)

    def test_empty_message_is_rejected(self):
        response = self.client.post("/api/chat", json={"message": "  "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_oversized_message_is_rejected(self):
        response = self.client.post("/api/chat", json={"message": "x" * 4001})
        self.assertEqual(response.status_code, 413)

    def test_fertilizer_fallback_avoids_invented_dosage(self):
        response = self.client.post(
            "/api/chat", json={"message": "What fertilizer dosage should I use?", "language": "en"}
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["source"], "safe_fallback")
        self.assertIn("won't guess", payload["reply"])
        self.assertIn("disclaimer", payload)

    def test_telugu_language_is_preserved(self):
        response = self.client.post(
            "/api/chat", json={"message": "పంట వ్యాధి ఏమిటి?", "language": "te"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["language"], "te")

    def test_unknown_language_defaults_to_english(self):
        response = self.client.post(
            "/api/chat", json={"message": "Hello", "language": "fr"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["language"], "en")


if __name__ == "__main__":
    unittest.main()
